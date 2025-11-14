/**
 * TaskMonitor Component
 *
 * Real-time task monitoring with WebSocket updates
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  MenuItem,
  Grid,
  Alert
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ApiService } from '../services/api';
import io from 'socket.io-client';

interface Task {
  id: string;
  task_type: string;
  agent_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  error_message?: string;
  result?: any;
}

const TaskMonitor: React.FC = () => {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Fetch tasks
  const { data: tasks = [], isLoading, error } = useQuery<Task[]>({
    queryKey: ['tasks', statusFilter, agentFilter],
    queryFn: async () => {
      const filters: any = {};
      if (statusFilter !== 'all') filters.status = statusFilter;
      if (agentFilter !== 'all') filters.agent_type = agentFilter;
      return ApiService.listTasks(filters);
    },
    refetchInterval: 5000
  });

  // Delete task mutation
  const deleteMutation = useMutation({
    mutationFn: (taskId: string) => ApiService.deleteTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    }
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    const socket = io('http://localhost:8000', {
      path: '/ws',
      transports: ['websocket']
    });

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setWsConnected(true);

      // Subscribe to task updates
      socket.emit('subscribe', { topic: 'tasks' });
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
    });

    socket.on('task_update', (data: any) => {
      console.log('Task update received:', data);
      // Invalidate tasks query to refresh data
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    });

    return () => {
      socket.disconnect();
    };
  }, [queryClient]);

  const getStatusColor = (status: string): 'default' | 'primary' | 'success' | 'error' => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const formatDuration = (task: Task): string => {
    if (!task.completed_at) return '-';
    const start = new Date(task.created_at).getTime();
    const end = new Date(task.completed_at).getTime();
    const duration = (end - start) / 1000;
    return `${duration.toFixed(2)}s`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Task Monitor
      </Typography>

      {/* Connection Status */}
      <Alert
        severity={wsConnected ? 'success' : 'warning'}
        sx={{ mb: 2 }}
      >
        WebSocket: {wsConnected ? 'Connected' : 'Disconnected'} - Real-time updates {wsConnected ? 'enabled' : 'disabled'}
      </Alert>

      {/* Filters */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <TextField
            select
            fullWidth
            label="Status Filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <MenuItem value="all">All Status</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
            <MenuItem value="running">Running</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
          </TextField>
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            select
            fullWidth
            label="Agent Filter"
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
          >
            <MenuItem value="all">All Agents</MenuItem>
            <MenuItem value="report">Report Agent</MenuItem>
            <MenuItem value="monitoring">Monitoring Agent</MenuItem>
            <MenuItem value="its">ITS Agent</MenuItem>
            <MenuItem value="db_extract">DB Extract Agent</MenuItem>
            <MenuItem value="change_mgmt">Change Management Agent</MenuItem>
            <MenuItem value="biz_support">Business Support Agent</MenuItem>
            <MenuItem value="sop">SOP Agent</MenuItem>
            <MenuItem value="infra">Infrastructure Agent</MenuItem>
          </TextField>
        </Grid>
      </Grid>

      {/* Tasks Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Task ID</TableCell>
              <TableCell>Agent Type</TableCell>
              <TableCell>Task Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created At</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Loading tasks...
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Alert severity="error">Error loading tasks</Alert>
                </TableCell>
              </TableRow>
            ) : tasks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  No tasks found
                </TableCell>
              </TableRow>
            ) : (
              tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {task.id.substring(0, 8)}...
                    </Typography>
                  </TableCell>
                  <TableCell>{task.agent_type}</TableCell>
                  <TableCell>{task.task_type}</TableCell>
                  <TableCell>
                    <Chip
                      label={task.status.toUpperCase()}
                      color={getStatusColor(task.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(task.created_at).toLocaleString()}
                  </TableCell>
                  <TableCell>{formatDuration(task)}</TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => setSelectedTask(task)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Task">
                      <IconButton
                        size="small"
                        onClick={() => deleteMutation.mutate(task.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Task Details Dialog */}
      {selectedTask && (
        <Paper sx={{ mt: 3, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Task Details
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Task ID
              </Typography>
              <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                {selectedTask.id}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Status
              </Typography>
              <Chip
                label={selectedTask.status.toUpperCase()}
                color={getStatusColor(selectedTask.status)}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Agent Type
              </Typography>
              <Typography variant="body1">
                {selectedTask.agent_type}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Task Type
              </Typography>
              <Typography variant="body1">
                {selectedTask.task_type}
              </Typography>
            </Grid>
            {selectedTask.error_message && (
              <Grid item xs={12}>
                <Alert severity="error">
                  <Typography variant="body2">
                    {selectedTask.error_message}
                  </Typography>
                </Alert>
              </Grid>
            )}
            {selectedTask.result && (
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Result
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                  <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                    {JSON.stringify(selectedTask.result, null, 2)}
                  </pre>
                </Paper>
              </Grid>
            )}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default TaskMonitor;
