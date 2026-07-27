import React from 'react';
import {
  ResponsiveContainer,
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';
import { Download } from 'lucide-react';
import { toPng } from 'html-to-image';

export interface ChartConfig {
  type: 'bar' | 'line' | 'pie';
  title?: string;
  data: any[];
}

interface DynamicChartProps {
  config: ChartConfig;
}

// Generate N visually distinct colors using HSL
const generateColors = (n: number): string[] => {
  return Array.from({ length: n }, (_, i) => {
    const hue = Math.round((i * 360) / n);
    const saturation = 65 + (i % 3) * 5; // 65–75%
    const lightness = 48 + (i % 2) * 8;  // 48–56%
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  });
};

const TOOLTIP_STYLE = {
  borderRadius: '8px',
  border: 'none',
  boxShadow: '0 4px 6px rgba(0,0,0,0.12)',
  fontSize: '13px',
};

// Custom scrollable legend component
const ScrollableLegend = ({
  items,
  colors,
}: {
  items: { name: string; value: number }[];
  colors: string[];
}) => (
  <div
    style={{
      maxHeight: '130px',
      overflowY: 'auto',
      display: 'flex',
      flexWrap: 'wrap',
      gap: '6px 14px',
      marginTop: '14px',
      paddingRight: '4px',
    }}
  >
    {items.map((item, i) => (
      <div
        key={item.name}
        style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', color: '#374151' }}
      >
        <span
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: colors[i % colors.length],
            flexShrink: 0,
            display: 'inline-block',
          }}
        />
        {item.name}
      </div>
    ))}
  </div>
);

const DynamicChart: React.FC<DynamicChartProps> = ({ config }) => {
  const { type, title, data } = config;
  const chartRef = React.useRef<HTMLDivElement>(null);

  const handleDownload = () => {
    if (chartRef.current) {
      toPng(chartRef.current, { 
        backgroundColor: '#ffffff', 
        pixelRatio: 2,
        filter: (node) => {
          if (node instanceof HTMLElement && node.classList.contains('hide-on-download')) {
            return false;
          }
          return true;
        }
      })
        .then((dataUrl) => {
          const link = document.createElement('a');
          link.download = `${title ? title.toLowerCase().replace(/\s+/g, '-') : 'finvox-chart'}.png`;
          link.href = dataUrl;
          link.click();
        })
        .catch((err) => console.error('Failed to download chart', err));
    }
  };

  if (!data || data.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
        No data available for chart.
      </div>
    );
  }

  // Find the label/name key (first string field)
  const nameKey =
    Object.keys(data[0]).find((k) => typeof data[0][k] === 'string') || 'name';

  // Find all numeric value keys
  const dataKeys = Object.keys(data[0]).filter(
    (k) => k !== nameKey && typeof data[0][k] === 'number'
  );
  const valueKey = dataKeys.length > 0 ? dataKeys[0] : 'value';

  // Generate unique colors for the full dataset
  const COLORS = generateColors(Math.max(data.length, 8));

  const renderChart = () => {
    // ── BAR CHART ─────────────────────────────────────────────────
    if (type === 'bar') {
      return (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: data.length > 6 ? 55 : 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey={nameKey}
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              angle={data.length > 6 ? -35 : 0}
              textAnchor={data.length > 6 ? 'end' : 'middle'}
              interval={0}
            />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: '#f8fafc' }} />
            {dataKeys.length > 0 ? (
              dataKeys.map((key, index) => (
                <Bar key={key} dataKey={key} fill={COLORS[index % COLORS.length]} radius={[4, 4, 0, 0]} isAnimationActive={false} />
              ))
            ) : (
              <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            )}
          </BarChart>
        </ResponsiveContainer>
      );
    }

    // ── LINE CHART ─────────────────────────────────────────────────
    if (type === 'line') {
      return (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey={nameKey} stroke="#64748b" fontSize={12} tickLine={false} />
            <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            {dataKeys.length > 0 ? (
              dataKeys.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={3}
                  dot={{ r: 4 }}
                  activeDot={{ r: 7 }}
                  isAnimationActive={false}
                />
              ))
            ) : (
              <Line type="monotone" dataKey="value" stroke={COLORS[0]} strokeWidth={3} activeDot={{ r: 7 }} isAnimationActive={false} />
            )}
          </LineChart>
        </ResponsiveContainer>
      );
    }

    // ── PIE CHART ─────────────────────────────────────────────────
    if (type === 'pie') {
      // Keep top 7 + group rest as "Others"
      const MAX_SLICES = 7;
      let chartData = data;
      if (data.length > MAX_SLICES) {
        const sorted = [...data].sort((a, b) => (b[valueKey] ?? 0) - (a[valueKey] ?? 0));
        const top = sorted.slice(0, MAX_SLICES);
        const othersValue = sorted.slice(MAX_SLICES).reduce((sum, d) => sum + (d[valueKey] ?? 0), 0);
        chartData = [...top, { [nameKey]: 'Others', [valueKey]: Math.round(othersValue) }];
      }
      const pieColors = generateColors(chartData.length);
      const legendItems = chartData.map((d) => ({ name: d[nameKey], value: d[valueKey] }));

      return (
        <div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Tooltip
                contentStyle={TOOLTIP_STYLE}
                formatter={(value: number, name: string) => [value.toLocaleString(), name]}
              />
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={110}
                dataKey={valueKey}
                nameKey={nameKey}
                isAnimationActive={false}
              >
                {chartData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={pieColors[index % pieColors.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <ScrollableLegend items={legendItems} colors={pieColors} />
        </div>
      );
    }

    return (
      <div style={{ color: '#e11d48', padding: '1rem' }}>Unsupported chart type: {type}</div>
    );
  };

  return (
    <div
      ref={chartRef}
      className="dynamic-chart-container"
      style={{
        background: 'white',
        borderRadius: '14px',
        padding: '1.5rem 1.5rem 1rem',
        margin: '1.5rem 0',
        boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
        border: '1px solid #e2e8f0',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', position: 'relative', marginBottom: '1.25rem', minHeight: '24px' }}>
        {title && (
          <h3
            style={{
              margin: '0',
              fontSize: '1rem',
              fontWeight: 700,
              color: '#1e293b',
              textAlign: 'center',
              letterSpacing: '-0.01em',
              flex: 1,
              paddingLeft: '32px', // Balance for center alignment
              paddingRight: '32px',
            }}
          >
            {title}
          </h3>
        )}
        <button
          className="hide-on-download"
          onClick={handleDownload}
          title="Download Chart"
          style={{
            position: 'absolute',
            top: '-4px',
            right: '-4px',
            background: 'transparent',
            border: 'none',
            color: '#64748b',
            cursor: 'pointer',
            padding: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '6px',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = '#1e293b';
            e.currentTarget.style.background = '#f1f5f9';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = '#64748b';
            e.currentTarget.style.background = 'transparent';
          }}
        >
          <Download size={18} />
        </button>
      </div>
      {renderChart()}
    </div>
  );
};

export default DynamicChart;
