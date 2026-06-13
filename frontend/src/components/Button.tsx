/**
 * 按钮组件
 * @author your-name
 */
import React from 'react';
import './Button.css';

interface ButtonProps {
  /** 按钮显示文本 */
  text: string;
  /** 点击事件回调 */
  onClick?: () => void;
  /** 是否禁用按钮 */
  disabled?: boolean;
  /** 按钮样式变体 */
  variant?: 'primary' | 'secondary' | 'danger';
}

/**
 * 按钮组件，支持多种样式变体和禁用状态
 * @param props - 组件属性
 */
const Button: React.FC<ButtonProps> = ({
  text,
  onClick = () => {},
  disabled = false,
  variant = 'primary'
}) => {
  const handleClick = () => {
    if (!disabled && onClick) {
      onClick();
    }
  };

  return (
    <button
      className={`btn btn-${variant}`}
      onClick={handleClick}
      disabled={disabled}
    >
      {text}
    </button>
  );
};

export default Button;