import React from 'react';
import { NavLink } from 'react-router-dom';
import { MessageSquare, BarChart2, FlaskConical, Shield, Settings } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { to: '/', icon: MessageSquare, label: 'Chat & RAG', exact: true },
    { to: '/evaluation', icon: BarChart2, label: 'Evaluation' },
    { to: '/experiment', icon: FlaskConical, label: 'Research Lab' },
  ];

  return (
    <div className="w-64 bg-slate-900 text-slate-100 flex flex-col h-full border-r border-slate-800">
      <div className="p-6 border-b border-slate-800 bg-slate-950">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-blue-500" />
          <div>
            <h1 className="text-xl font-bold tracking-tight">DocSentry</h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">AI Auditor</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
              }`
            }
          >
            <item.icon className={`w-5 h-5 transition-colors ${
              (isActive) => isActive ? 'text-white' : 'group-hover:text-blue-400'
            }`} />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button className="flex items-center gap-3 px-4 py-3 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 w-full transition-all">
          <Settings className="w-5 h-5" />
          <span className="font-medium">Settings</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
