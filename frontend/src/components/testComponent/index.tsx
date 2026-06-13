import React from 'react'
import './index.css'

interface TextDisplayProps {
  text?: string;
  title?: string;
  className?: string;
}

const TextDisplay: React.FC<TextDisplayProps> = ({
  text = '默认文本内容',
  title,
  className = ''
}) => {
  return (
    <div className={`text-display ${className}`}>
      {title && <h2 className="text-display-title">{title}</h2>}
      <p className="text-display-content">{text}</p>
    </div>
  )
}

export default TextDisplay
