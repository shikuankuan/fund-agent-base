import { useState } from 'react'
import './App.css'
import TextDisplay from './components/testComponent'
import ButtonDemo from './components/ButtonDemo'
import EnhancedButtonDemo from './components/EnhancedButtonDemo'

function App() {
  const [message] = useState("Hello Fund Agent! 🚀")

  return (
    <div className="app">
      <h1>{message}</h1>
      <p>基金行业 Agent 智能体 - Day 1 环境搭建完成 ✅</p>

      <div style={{ marginTop: '40px' }}>
        <TextDisplay
          title="欢迎使用文本展示组件"
          text="这是一个简单的React组件，用于展示文本内容。您可以自定义标题和文本内容，也可以通过className属性添加自定义样式。"
        />

        <TextDisplay
          title="另一个示例"
          text="您可以多次使用此组件来展示不同的文本内容。每个实例都可以独立配置。"
        />

        <TextDisplay
          text="没有标题的文本展示组件示例。"
        />
      </div>

      <div style={{ marginTop: '40px' }}>
        <ButtonDemo />
      </div>

      <div style={{ marginTop: '40px' }}>
        <EnhancedButtonDemo />
      </div>
    </div>
  )
}

export default App