import { NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? 'active' : ''

  return (
    <div className="app-layout">
      <nav className="app-nav">
        <span className="nav-brand">
          <span>🤖</span> AI 面试训练 Agent
        </span>
        <span className="nav-links">
          <NavLink to="/" end className={linkClass}>首页</NavLink>
          <NavLink to="/jd-input" className={linkClass}>开始面试</NavLink>
          <NavLink to="/eval" className={linkClass}>评测面板</NavLink>
        </span>
      </nav>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
