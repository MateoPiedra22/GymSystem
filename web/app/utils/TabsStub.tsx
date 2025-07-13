import React from 'react';

export function Tabs({ value, onValueChange, children, className }: any) {
  return <div className={className}>{React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      const c: any = child;
      return React.cloneElement(c, { selected: (c.props as any).value === value, onSelect: () => onValueChange((c.props as any).value) });
    }
    return child;
  })}</div>;
}

export function Tab({ value, label, selected, onSelect }: any) {
  return (
    <button
      type="button"
      onClick={onSelect}
      style={{ fontWeight: selected ? 'bold' : 'normal', marginRight: 8 }}
    >
      {label}
    </button>
  );
} 