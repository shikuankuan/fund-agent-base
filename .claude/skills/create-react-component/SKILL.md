---
name: create-react-component
description: 创建标准的React函数组件，使用TypeScript、Props接口、默认值和适当的注释
version: 1.0.0
author: Claude Assistant
tags: ["react", "typescript", "component"]
compatibility: ["claude-code"]
examples:
  - "创建一个React按钮组件"
  - "用create-react-component创建一个表单组件"
---

## React组件创建指南

当用户请求创建React组件时，请按照以下规范生成代码：

### 要求
1. 使用函数式组件和TypeScript
2. 定义清晰的Props接口，包含JSDoc注释
3. 为Props提供合理的默认值
4. 包含适当的导入语句
5. 添加文件头和组件级注释
6. 使用export default导出组件
7. 遵循2空格缩进规范

### 模板
```tsx
/**
 * 组件描述
 * @author author-name
 */
import React from 'react';

interface ComponentProps {
  /** 属性描述 */
  prop1: string;
  /** 属性描述 */
  prop2?: boolean;
}

/**
 * 组件描述
 * @param props - 组件属性
 */
const ComponentName: React.FC<ComponentProps> = ({
  prop1,
  prop2 = false
}) => {
  return (
    <div>
      {/* 组件内容 */}
    </div>
  );
};

export default ComponentName;
```