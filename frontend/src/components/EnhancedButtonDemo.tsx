/**
 * 增强按钮组件演示
 * @author Claude
 */
import React from 'react';
import EnhancedButton from './EnhancedButton';

const EnhancedButtonDemo: React.FC = () => {
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Enhanced Button 演示</h2>

      <div className="space-y-4">
        <div>
          <h3 className="font-semibold mb-2">不同变体</h3>
          <div className="flex flex-wrap gap-2">
            <EnhancedButton>Primary</EnhancedButton>
            <EnhancedButton variant="secondary">Secondary</EnhancedButton>
            <EnhancedButton variant="outline">Outline</EnhancedButton>
            <EnhancedButton variant="ghost">Ghost</EnhancedButton>
            <EnhancedButton variant="destructive">Destructive</EnhancedButton>
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-2">不同尺寸</h3>
          <div className="flex flex-wrap items-center gap-2">
            <EnhancedButton size="small">Small</EnhancedButton>
            <EnhancedButton size="medium">Medium</EnhancedButton>
            <EnhancedButton size="large">Large</EnhancedButton>
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-2">状态</h3>
          <div className="flex flex-wrap gap-2">
            <EnhancedButton disabled>Disabled</EnhancedButton>
            <EnhancedButton loading>Loading</EnhancedButton>
            <EnhancedButton loading loadingText="Loading...">
              Submit
            </EnhancedButton>
          </div>
        </div>

        <div>
          <h3 className="font-semibold mb-2">带图标的按钮</h3>
          <div className="flex flex-wrap gap-2">
            <EnhancedButton iconBefore={<span>+</span>}>添加</EnhancedButton>
            <EnhancedButton iconAfter={<span>→</span>}>下一步</EnhancedButton>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedButtonDemo;