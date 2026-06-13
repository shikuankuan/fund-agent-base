/**
 * 增强按钮组件 - 支持更多样式选项和功能
 * @author Claude
 */
import React from 'react';

interface EnhancedButtonProps {
  /** 按钮显示内容（可以是文本或JSX元素） */
  children: React.ReactNode;
  /** 按钮点击事件 */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** 按钮类型 */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  /** 按钮大小 */
  size?: 'small' | 'medium' | 'large';
  /** 是否禁用按钮 */
  disabled?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 按钮类型（HTML原生属性） */
  type?: 'button' | 'submit' | 'reset';
  /** 是否为加载状态 */
  loading?: boolean;
  /** 加载时显示的文本 */
  loadingText?: string;
  /** 按钮的图标前置元素 */
  iconBefore?: React.ReactNode;
  /** 按钮的图标后置元素 */
  iconAfter?: React.ReactNode;
}

/**
 * 增强按钮组件 - 提供多种样式变体、尺寸选项和额外功能
 * @param props - 组件属性
 */
const EnhancedButton: React.FC<EnhancedButtonProps> = ({
  children,
  onClick = () => {},
  variant = 'primary',
  size = 'medium',
  disabled = false,
  className = '',
  type = 'button',
  loading = false,
  loadingText,
  iconBefore,
  iconAfter
}) => {
  // 合并所有状态相关的禁用情况
  const isDisabled = disabled || loading;

  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none';

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-600 disabled:bg-blue-300',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus-visible:ring-gray-200 disabled:bg-gray-100',
    outline: 'border border-blue-600 text-blue-600 hover:bg-blue-50 focus-visible:ring-blue-600 disabled:border-gray-300 disabled:text-gray-400',
    ghost: 'text-gray-900 hover:bg-gray-100 focus-visible:ring-gray-200 disabled:text-gray-400',
    destructive: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-600 disabled:bg-red-300'
  };

  const sizeClasses = {
    small: 'h-8 px-3 text-sm',
    medium: 'h-10 px-4 py-2',
    large: 'h-12 px-6 text-lg'
  };

  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;

  return (
    <button
      className={classes}
      onClick={onClick}
      disabled={isDisabled}
      type={type}
      aria-busy={loading}
    >
      {loading ? (
        <>
          <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
          {loadingText || children}
        </>
      ) : (
        <>
          {iconBefore && <span className="mr-2">{iconBefore}</span>}
          {children}
          {iconAfter && <span className="ml-2">{iconAfter}</span>}
        </>
      )}
    </button>
  );
};

export default EnhancedButton;