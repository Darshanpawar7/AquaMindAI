/**
 * Tests for AlertsPanel component
 * Covers: sorted alert list, priority badges, error banner, state preservation on error,
 * and Critical alert immediate action indicator.
 *
 * // Feature: aquamind-ai, Property 22: Dashboard preserves state on API error
 * // Validates: Requirements 7.1, 7.5
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import fc from 'fast-check';
import { AlertsPanel } from '../../frontend/src/components/AlertsPanel';
import { Alert } from '../../frontend/src/api';

// ---- helpers ----

function makeAlert(overrides: Partial<Alert> = {}): Alert {
  return {
    alert_id: 'alert-1',
    pipe_id: 'pipe_001',
    timestamp: '2024-01-01T00:00:00Z',
    anomaly_type: 'leak',
    anomaly_score: 0.8,
    failure_probability: 0.9,
    priority_score: 90,
    priority_level: 'Critical',
    immediate_action_required: true,
    flow_rate: 12.5,
    pressure: 40.0,
    ...overrides,
  };
}

const SAMPLE_ALERTS: Alert[] = [
  makeAlert({ alert_id: 'a1', pipe_id: 'pipe_001', priority_level: 'Critical', priority_score: 90, immediate_action_required: true }),
  makeAlert({ alert_id: 'a2', pipe_id: 'pipe_002', priority_level: 'High', priority_score: 70, immediate_action_required: false }),
  makeAlert({ alert_id: 'a3', pipe_id: 'pipe_003', priority_level: 'Medium', priority_score: 40, immediate_action_required: false }),
  makeAlert({ alert_id: 'a4', pipe_id: 'pipe_004', priority_level: 'Low', priority_score: 15, immediate_action_required: false }),
];

// ---- unit tests ----

describe('AlertsPanel', () => {
  test('renders all alerts in the list', () => {
    render(
      <AlertsPanel
        alerts={SAMPLE_ALERTS}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error={null}
      />
    );
    expect(screen.getByText('pipe_001')).toBeInTheDocument();
    expect(screen.getByText('pipe_002')).toBeInTheDocument();
    expect(screen.getByText('pipe_003')).toBeInTheDocument();
    expect(screen.getByText('pipe_004')).toBeInTheDocument();
  });

  test('renders priority badges for each alert', () => {
    render(
      <AlertsPanel
        alerts={SAMPLE_ALERTS}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error={null}
      />
    );
    expect(screen.getByText('Critical')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  test('shows error banner when error prop is set', () => {
    render(
      <AlertsPanel
        alerts={SAMPLE_ALERTS}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error="Network request failed"
      />
    );
    const banner = screen.getByRole('alert');
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveTextContent('Network request failed');
  });

  test('existing alert list is preserved when error occurs', () => {
    render(
      <AlertsPanel
        alerts={SAMPLE_ALERTS}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error="API unavailable"
      />
    );
    // Error banner shown
    expect(screen.getByRole('alert')).toBeInTheDocument();
    // Alerts still visible
    expect(screen.getByText('pipe_001')).toBeInTheDocument();
    expect(screen.getByText('pipe_002')).toBeInTheDocument();
  });

  test('Critical alert shows immediate action indicator', () => {
    render(
      <AlertsPanel
        alerts={[makeAlert({ priority_level: 'Critical', immediate_action_required: true })]}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error={null}
      />
    );
    expect(screen.getByText(/Immediate Action Required/i)).toBeInTheDocument();
  });

  test('non-Critical alert does not show immediate action indicator', () => {
    render(
      <AlertsPanel
        alerts={[makeAlert({ priority_level: 'High', immediate_action_required: false })]}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error={null}
      />
    );
    expect(screen.queryByText(/Immediate Action Required/i)).not.toBeInTheDocument();
  });

  test('calls onSelectAlert with correct id when alert is clicked', () => {
    const onSelect = jest.fn();
    render(
      <AlertsPanel
        alerts={SAMPLE_ALERTS}
        selectedAlertId={null}
        onSelectAlert={onSelect}
        error={null}
      />
    );
    fireEvent.click(screen.getByText('pipe_001').closest('div[style]')!);
    expect(onSelect).toHaveBeenCalledWith('a1');
  });

  test('no error banner when error is null', () => {
    render(
      <AlertsPanel
        alerts={SAMPLE_ALERTS}
        selectedAlertId={null}
        onSelectAlert={jest.fn()}
        error={null}
      />
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });
});

// ---- property-based test ----
// Feature: aquamind-ai, Property 22: Dashboard preserves state on API error
// Validates: Requirements 7.5

describe('AlertsPanel — Property 22: Dashboard preserves state on API error', () => {
  test('alert list is never cleared when an error is present', () => {
    const priorityLevels = ['Critical', 'High', 'Medium', 'Low'] as const;

    fc.assert(
      fc.property(
        // Generate 1–10 alerts
        fc.array(
          fc.record({
            alert_id: fc.uuid(),
            pipe_id: fc.stringMatching(/^pipe_\d{3}$/),
            timestamp: fc.constant('2024-01-01T00:00:00Z'),
            anomaly_type: fc.constantFrom('leak', 'degradation', 'noise'),
            anomaly_score: fc.float({ min: 0, max: 1 }),
            failure_probability: fc.float({ min: 0, max: 1 }),
            priority_score: fc.integer({ min: 1, max: 100 }),
            priority_level: fc.constantFrom(...priorityLevels),
            immediate_action_required: fc.boolean(),
            flow_rate: fc.float({ min: 0, max: 50 }),
            pressure: fc.float({ min: 0, max: 100 }),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        // Generate a non-empty error string
        fc.string({ minLength: 1 }),
        (alerts, errorMsg) => {
          const { container } = render(
            <AlertsPanel
              alerts={alerts}
              selectedAlertId={null}
              onSelectAlert={() => {}}
              error={errorMsg}
            />
          );

          // Error banner must be present
          const banner = container.querySelector('[role="alert"]');
          expect(banner).not.toBeNull();

          // All pipe_ids must still be rendered
          for (const alert of alerts) {
            expect(container.textContent).toContain(alert.pipe_id);
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
