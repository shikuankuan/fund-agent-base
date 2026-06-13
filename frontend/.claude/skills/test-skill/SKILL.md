---
name: write-react-component
description: 编写标准 React 函数组件，使用 TypeScript、Props 接口、默认值、注释、导出格式。适用于：创建新组件、重构组件、写业务组件。
version: 1.0.0
author: your-name
tags: ["react", "typescript", "frontend"]
compatibility: ["claude-code"]
examples:
  - "帮我写一个 React 组件"
  - "用 write-react-component 写一个按钮组件"
---
## React 组件编写规范

### 必须遵守
1. 使用函数组件 + TypeScript
2. 定义 Props 接口，必须有注释
3. 给 Props 设置默认值
4. 使用 2 空格缩进
5. 必须有文件头部注释、组件注释
6. 使用 export default 导出

### 模板
```tsx
/**
 * 组件功能描述
 * @author your-name
 */
import React from 'react';

interface ComponentProps {
  /** 说明 */
  title: string;
  /** 说明 */
  onClick?: () => void;
}

const defaultProps: Partial<ComponentProps> = {
  onClick: () => {},
};

/**
 * 组件描述
 * @param props - 组件属性
 */
const MyComponent: React.FC<ComponentProps> = (props) => {
  const { title, onClick } = props;
  return <button onClick={onClick}>{title}</button>;
};

MyComponent.defaultProps = defaultProps;

export default MyComponent;