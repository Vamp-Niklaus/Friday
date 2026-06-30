import { Check, Pencil, X, AlertCircle } from "lucide-react";
import { useEffect, useState } from "react";

import {
  Task,
  TaskGroup,
  completeTask,
  listOpenTodos,
  updateTaskTitle,
} from "../services/api";

function formatDate(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

export function TodosPage() {
  const [groups, setGroups] = useState<TaskGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  async function loadTodos() {
    try {
      setLoading(true);
      const data = await listOpenTodos();
      setGroups(data.groups);
      setError(null);
    } catch (err) {
      setError("Failed to load todos.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTodos();
  }, []);

  function startEdit(task: Task) {
    setEditingId(task.id);
    setEditTitle(task.title);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditTitle("");
  }

  async function saveEdit(taskId: string) {
    const trimmed = editTitle.trim();
    if (!trimmed) return;
    try {
      await updateTaskTitle(taskId, trimmed);
      cancelEdit();
      await loadTodos();
    } catch {
      setError("Failed to update task.");
    }
  }

  async function handleComplete(taskId: string) {
    try {
      await completeTask(taskId);
      await loadTodos();
    } catch {
      setError("Failed to complete task.");
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h2>Todos</h2>
      </header>

      {loading && <p className="muted">Loading...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && groups.length === 0 && (
        <p className="muted">No open todos. Create one from the Chat page.</p>
      )}

      {groups.map((group) => {
        const isPastDue = new Date(group.date).getTime() < Date.now();
        return (
        <section className="task-group" key={group.date}>
          <h3 className="task-group-date" style={{ color: isPastDue ? '#ef4444' : 'inherit' }}>
            {formatDate(group.date)}
            {isPastDue && <span style={{ marginLeft: '8px', fontSize: '0.85em', display: 'inline-flex', alignItems: 'center', gap: '4px' }}><AlertCircle size={14} /> Past Due</span>}
          </h3>
          <ul className="task-list">
            {group.tasks.map((task) => (
              <li className="task-item" key={task.id}>
                {editingId === task.id ? (
                  <div className="task-edit">
                    <input
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      autoFocus
                    />
                    <button className="icon-button" onClick={() => saveEdit(task.id)} title="Save">
                      <Check size={16} />
                    </button>
                    <button className="icon-button" onClick={cancelEdit} title="Cancel">
                      <X size={16} />
                    </button>
                  </div>
                ) : (
                  <>
                    <span className="task-title">
                      {task.title}
                      {task.metadata?.url && (
                        <a href={task.metadata.url as string} target="_blank" rel="noreferrer" style={{ marginLeft: '8px', fontSize: '0.85em', color: '#0288d1' }}>[Link]</a>
                      )}
                    </span>
                    <div className="task-actions">
                      <button
                        className="icon-button"
                        onClick={() => startEdit(task)}
                        title="Edit"
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        className="icon-button icon-button-primary"
                        onClick={() => handleComplete(task.id)}
                        title="Mark complete"
                      >
                        <Check size={16} />
                      </button>
                    </div>
                  </>
                )}
              </li>
            ))}
          </ul>
        </section>
        );
      })}
    </div>
  );
}
