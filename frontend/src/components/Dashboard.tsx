/**
 * Dashboard Component
 *
 * Main dashboard showing system overview and statistics
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  PlayArrow as RunningIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import ApiService from '../services/api';

interface DashboardData {
  overview: {
    total_tasks: number;
    success_rate: number;
    active_agents: number;
    system_health: string;
  };
  tasks: {
    total: number;
    pending: number;
    running: number;
    completed: number;
    failed: number;
    success_rate: number;
  };
  agents: Record<string, any>;
  recent_tasks: any[];
  recent_executions: any[];
  system: {
    cpu_percent: number;
    memory_percent: number;
  };
}

const Dashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => ApiService.getDashboardData(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (isLoading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading dashboard...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">Failed to load dashboard data</Typography>
      </Box>
    );
  }

  if (!data) return null;

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'degraded':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Tasks
              </Typography>
              <Typography variant="h4">{data.overview.total_tasks}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h4">
                {data.overview.success_rate.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={data.overview.success_rate}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Agents
              </Typography>
              <Typography variant="h4">{data.overview.active_agents}</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                System Health
              </Typography>
              <Chip
                label={data.overview.system_health.toUpperCase()}
                color={getHealthColor(data.overview.system_health) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Task Statistics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Task Statistics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box display="flex" alignItems="center" mb={1}>
                  <PendingIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  <Typography>Pending: {data.tasks.pending}</Typography>
                </Box>
                <Box display="flex" alignItems="center" mb={1}>
                  <RunningIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography>Running: {data.tasks.running}</Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box display="flex" alignItems="center" mb={1}>
                  <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography>Completed: {data.tasks.completed}</Typography>
                </Box>
                <Box display="flex" alignItems="center" mb={1}>
                  <ErrorIcon sx={{ mr: 1, color: 'error.main' }} />
                  <Typography>Failed: {data.tasks.failed}</Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* System Resources */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              System Resources
            </Typography>
            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">
                CPU Usage: {data.system.cpu_percent.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={data.system.cpu_percent}
                sx={{ mt: 1 }}
              />
            </Box>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Memory Usage: {data.system.memory_percent.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={data.system.memory_percent}
                sx={{ mt: 1 }}
              />
            </Box>
          </Paper>
        </Grid>

        {/* Recent Tasks */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Tasks
            </Typography>
            {data.recent_tasks.map((task) => (
              <Box
                key={task.id}
                sx={{
                  p: 1,
                  mb: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                }}
              >
                <Typography variant="body2">
                  <strong>{task.agent}</strong> - {task.type}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Status: {task.status} | {new Date(task.created_at).toLocaleTimeString()}
                </Typography>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Agent Statistics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Agent Statistics
            </Typography>
            {Object.entries(data.agents).map(([agentType, stats]: [string, any]) => (
              <Box
                key={agentType}
                sx={{
                  p: 1,
                  mb: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                }}
              >
                <Typography variant="body2">
                  <strong>{agentType}</strong>
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Total: {stats.total} | Success: {stats.completed} | Failed: {stats.failed} |
                  Rate: {stats.success_rate.toFixed(1)}%
                </Typography>
              </Box>
            ))}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
