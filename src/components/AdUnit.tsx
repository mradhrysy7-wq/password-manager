import React from 'react';

interface AdUnitProps {
  slot?: string;
}

export const AdUnit: React.FC<AdUnitProps> = () => {
  return (
    <div className="ad-wrap" aria-label="إعلان" role="region">
      <div style={{ opacity: 0.6, fontSize: '13px' }}>
        📢 مساحة إعلانية متوافقة مع Google AdSense
      </div>
    </div>
  );
};
