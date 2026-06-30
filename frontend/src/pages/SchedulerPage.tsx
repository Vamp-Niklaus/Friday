import { Repeat, Trash2, Settings, ArrowLeft, ChevronDown, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";

import {
  ProblemQueueResponse,
  Task,
  reviseProblem,
  deleteTask,
  getProblemQueue,
  updateQueueSettings,
} from "../services/api";

type TabView = 'overview' | 'today' | 'upcoming' | 'completed';

export function SchedulerPage() {
  const [queue, setQueue] = useState<ProblemQueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showPastDue, setShowPastDue] = useState(false);
  const [activeTab, setActiveTab] = useState<TabView>('overview');

  async function loadData() {
    try {
      setLoading(true);
      const data = await getProblemQueue();
      setQueue(data);
      setError(null);
    } catch (err) {
      setError("Failed to load problem queue.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleRevise(taskId: string) {
    try {
      await reviseProblem(taskId);
      await loadData();
    } catch {
      setError("Failed to mark problem as revised.");
    }
  }

  async function handleDelete(taskId: string) {
    if (!window.confirm("Are you sure you want to delete this problem?")) return;
    try {
      await deleteTask(taskId);
      await loadData();
    } catch {
      setError("Failed to delete problem.");
    }
  }



  if (loading && !queue) return <div className="page"><p className="muted">Loading queue...</p></div>;

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tomorrowStr = tomorrow.toISOString().split('T')[0];
  const tomorrowTasks = queue?.upcoming.filter(t => t.todo_at.startsWith(tomorrowStr)) || [];

  const renderTaskList = (tasks: Task[], title: string, showDate: boolean, emptyMsg: string) => (
    <section className="task-group" style={{ marginTop: '24px' }}>
      <h3 className="task-group-date">{title} ({tasks.length})</h3>
      {tasks.length === 0 ? (
        <p className="muted">{emptyMsg}</p>
      ) : (
        <ul className="task-list">
          {tasks.map((task: Task) => (
            <li className="task-item" key={task.id} style={{ borderLeft: '4px solid #0288d1' }}>
              <span className="task-title">
                {showDate && task.formatted_date && (
                  <span style={{ color: '#0288d1', fontWeight: 600, marginRight: '8px' }}>[{task.formatted_date}]</span>
                )}
                <span>
                  {task.title}
                </span>
                {task.metadata?.url && (
                  <a href={task.metadata.url as string} target="_blank" rel="noreferrer" style={{ marginLeft: '8px', fontSize: '0.85em', color: '#0288d1' }}>[Link]</a>
                )}
              </span>
              <div className="task-actions" style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="icon-button icon-button-primary"
                  onClick={() => handleRevise(task.id)}
                  title="Mark as revised (Schedules for next interval)"
                  style={{ backgroundColor: '#2e7d32' }}
                >
                  <Repeat size={16} />
                </button>
                <button
                  className="icon-button icon-button-danger"
                  onClick={() => handleDelete(task.id)}
                  title="Delete problem"
                  style={{ backgroundColor: '#d32f2f' }}
                >
                  <Trash2 size={16} color="#fff" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );

  const renderGroupedTaskList = (tasks: Task[], title: string, emptyMsg: string, useLastRevisedTime = false) => {
    if (tasks.length === 0) {
      return (
        <section className="task-group" style={{ marginTop: '24px' }}>
          <h3 className="task-group-date">{title} (0)</h3>
          <p className="muted">{emptyMsg}</p>
        </section>
      );
    }

    const groups: Record<string, Task[]> = {};
    for (const t of tasks) {
      let dateObj = new Date(t.todo_at);
      if (useLastRevisedTime && t.metadata?.last_revised_at) {
        dateObj = new Date(t.metadata.last_revised_at as string);
      }
      
      const dateKey = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(t);
    }

    const sortedDates = Object.keys(groups).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
    // If it's the Solved Today view, reverse the dates so most recent is first
    if (useLastRevisedTime) sortedDates.reverse();

    return (
      <section className="task-group" style={{ marginTop: '24px' }}>
        <h3 className="task-group-date">{title} ({tasks.length})</h3>
        {sortedDates.map(dateKey => (
          <div key={dateKey} style={{ marginTop: '24px' }}>
            <h4 style={{ margin: '0 0 12px 0', borderBottom: '2px solid #eee', paddingBottom: '6px', color: '#333' }}>{dateKey}</h4>
            <ul className="task-list">
              {groups[dateKey].map((task: Task) => {
                let timeObj = new Date(task.todo_at);
                if (useLastRevisedTime && task.metadata?.last_revised_at) {
                  timeObj = new Date(task.metadata.last_revised_at as string);
                }
                const timeStr = timeObj.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                
                return (
                  <li className="task-item" key={task.id} style={{ borderLeft: useLastRevisedTime ? '4px solid #4caf50' : '4px solid #0288d1' }}>
                    <span className="task-title">
                      <span style={{ color: useLastRevisedTime ? '#388e3c' : '#0288d1', fontWeight: 600, marginRight: '8px' }}>[{timeStr}]</span>
                      <span style={{ textDecoration: useLastRevisedTime ? 'line-through' : 'none', opacity: useLastRevisedTime ? 0.7 : 1 }}>
                        {task.title}
                      </span>
                      {task.metadata?.url && (
                        <a href={task.metadata.url as string} target="_blank" rel="noreferrer" style={{ marginLeft: '8px', fontSize: '0.85em', color: '#0288d1' }}>[Link]</a>
                      )}
                    </span>
                    {!useLastRevisedTime && (
                      <div className="task-actions" style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="icon-button icon-button-primary"
                          onClick={() => handleRevise(task.id)}
                          title="Mark as revised"
                          style={{ backgroundColor: '#2e7d32' }}
                        >
                          <Repeat size={16} />
                        </button>
                        <button
                          className="icon-button icon-button-danger"
                          onClick={() => handleDelete(task.id)}
                          title="Delete problem"
                          style={{ backgroundColor: '#d32f2f' }}
                        >
                          <Trash2 size={16} color="#fff" />
                        </button>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </section>
    );
  };

  return (
    <div className="page">
      <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {activeTab !== 'overview' && (
            <button className="icon-button" onClick={() => setActiveTab('overview')} title="Back to Overview">
              <ArrowLeft size={24} />
            </button>
          )}
          <h2>{activeTab === 'overview' ? 'Scheduler Overview' : activeTab === 'today' ? 'Due Today' : activeTab === 'upcoming' ? 'All Upcoming' : 'Solved Today'}</h2>
        </div>
      </header>

      {error && <p className="error">{error}</p>}



      {queue && activeTab === 'overview' && (
        <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
          <div 
            style={{ background: '#e1f5fe', padding: '12px 16px', borderRadius: '8px', flex: 1, cursor: 'pointer', transition: 'background 0.2s' }}
            onClick={() => setActiveTab('today')}
            onMouseOver={e => e.currentTarget.style.background = '#b3e5fc'}
            onMouseOut={e => e.currentTarget.style.background = '#e1f5fe'}
          >
            <h4 style={{ margin: '0 0 4px 0', color: '#0277bd' }}>Due Today</h4>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#01579b' }}>{queue.due_today.length}</span>
          </div>
          <div 
            style={{ background: '#f5f5f5', padding: '12px 16px', borderRadius: '8px', flex: 1, cursor: 'pointer', transition: 'background 0.2s' }}
            onClick={() => setActiveTab('upcoming')}
            onMouseOver={e => e.currentTarget.style.background = '#e0e0e0'}
            onMouseOut={e => e.currentTarget.style.background = '#f5f5f5'}
          >
            <h4 style={{ margin: '0 0 4px 0', color: '#616161' }}>Upcoming</h4>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#424242' }}>{queue.upcoming.length}</span>
          </div>
          <div 
            style={{ background: '#e8f5e9', padding: '12px 16px', borderRadius: '8px', flex: 1, cursor: 'pointer', transition: 'background 0.2s' }}
            onClick={() => setActiveTab('completed')}
            onMouseOver={e => e.currentTarget.style.background = '#c8e6c9'}
            onMouseOut={e => e.currentTarget.style.background = '#e8f5e9'}
          >
            <h4 style={{ margin: '0 0 4px 0', color: '#2e7d32' }}>Solved Today</h4>
            <span style={{ fontSize: '24px', fontWeight: 'bold', color: '#1b5e20' }}>{queue.actual_completed}</span>
          </div>
        </div>
      )}

      {queue && (
        <>
          {activeTab === 'overview' && (
            <>
              {queue.past_due && queue.past_due.length > 0 && (
                <section className="task-group" style={{ marginTop: '24px', background: '#fff3e0', padding: '16px', borderRadius: '8px' }}>
                  <div 
                    style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                    onClick={() => setShowPastDue(!showPastDue)}
                  >
                    {showPastDue ? <ChevronDown size={20} color="#e65100" /> : <ChevronRight size={20} color="#e65100" />}
                    <h3 style={{ margin: '0 0 0 8px', color: '#e65100' }}>Past Due ({queue.past_due.length})</h3>
                  </div>
                  
                  {showPastDue && (
                    <div style={{ marginTop: '16px' }}>
                      <ul className="task-list">
                        {queue.past_due.map((task: Task) => (
                          <li className="task-item" key={task.id} style={{ borderLeft: '4px solid #ef6c00', background: 'white' }}>
                            <span className="task-title">
                              <span style={{ color: '#d84315', fontWeight: 600, marginRight: '8px' }}>[{task.formatted_date}]</span>
                              <span>{task.title}</span>
                              {task.metadata?.url && (
                                <a href={task.metadata.url as string} target="_blank" rel="noreferrer" style={{ marginLeft: '8px', fontSize: '0.85em', color: '#0288d1' }}>[Link]</a>
                              )}
                            </span>
                            <div className="task-actions" style={{ display: 'flex', gap: '8px' }}>
                              <button
                                className="icon-button icon-button-primary"
                                onClick={() => handleRevise(task.id)}
                                title="Mark as revised"
                                style={{ backgroundColor: '#2e7d32' }}
                              >
                                <Repeat size={16} />
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </section>
              )}
              
              {renderTaskList(queue.due_today, "Due Today", false, "All caught up for today!")}
              <div style={{ opacity: 0.8 }}>
                {renderTaskList(tomorrowTasks, "Upcoming Tomorrow", false, "No problems scheduled for tomorrow.")}
              </div>
            </>
          )}

          {activeTab === 'today' && (
            <>
              {queue.past_due && queue.past_due.length > 0 && renderTaskList(queue.past_due, "Past Due", true, "")}
              {renderTaskList(queue.due_today, "Due Today", false, "All caught up for today!")}
            </>
          )}
          
          {activeTab === 'upcoming' && renderGroupedTaskList(queue.upcoming, "All Upcoming Problems", "No upcoming problems in the queue.")}
          
          {activeTab === 'completed' && renderGroupedTaskList(queue.solved_today || [], "Solved Today", "You haven't reviewed any problems today.", true)}
        </>
      )}
    </div>
  );
}
