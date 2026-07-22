import { Brain, House, List, Play, X } from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const linkClass = ({ isActive }: { isActive: boolean }) => isActive ? 'active' : ''

  return (
    <div className="app-layout">
      <header className="app-nav">
        <div className="nav-inner">
          <Link to="/" className="nav-brand" aria-label="面试练习室首页">
            <span className="brand-mark"><Brain weight="fill" /></span><span>面试练习室</span><span className="brand-tag">AI</span>
          </Link>
          <button className="nav-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? '关闭导航菜单' : '打开导航菜单'}>{menuOpen ? <X /> : <List />}</button>
          <nav className={`nav-links ${menuOpen ? 'open' : ''}`} onClick={() => setMenuOpen(false)}>
            <NavLink to="/" end className={linkClass}><House />首页</NavLink>
            <NavLink to="/jd-input" className={linkClass}><Play weight="fill" />开始训练</NavLink>
            <Link to="/?section=pricing" className="nav-pricing">套餐价格</Link>
          </nav>
        </div>
      </header>
      <main className="app-main"><Outlet /></main>
      <footer className="app-footer">
        <div><strong>面试练习室</strong><span>让每一次练习，都变成下一次进步。</span></div>
        <span>AI 生成内容仅供求职准备参考，不承诺面试结果</span>
      </footer>
    </div>
  )
}
