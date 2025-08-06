import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';

const App = () => {
  const [tasks, setTasks] = React.useState([]);

  React.useEffect(() => {
    fetch('http://localhost:8000/tasks/')
      .then(response => response.json())
      .then(data => setTasks(data));
  }, []);

  return (
    <div>
      <h1>Tasks</h1>
      <ul>
        {tasks.map(task => (
          <li key={task.id}>{task.name}</li>
        ))}
      </ul>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
