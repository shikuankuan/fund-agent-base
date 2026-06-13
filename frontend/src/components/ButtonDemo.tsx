import React, { useState } from 'react';
import Button from './Button';

const ButtonDemo: React.FC = () => {
  const [count, setCount] = useState(0);

  const handleIncrement = () => {
    setCount(count + 1);
  };

  const handleDecrement = () => {
    setCount(count - 1);
  };

  const handleReset = () => {
    setCount(0);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>按钮组件演示</h2>
      <p>计数器值: {count}</p>

      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <Button text="增加" onClick={handleIncrement} variant="primary" />
        <Button text="减少" onClick={handleDecrement} variant="secondary" />
        <Button text="重置" onClick={handleReset} variant="danger" />
        <Button text="禁用按钮" disabled={true} variant="primary" />
      </div>
    </div>
  );
};

export default ButtonDemo;