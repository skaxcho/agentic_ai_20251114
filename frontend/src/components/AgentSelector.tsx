/**
 * Agent Selector Component
 *
 * Component for selecting and executing agent tasks
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
} from '@mui/material';
import { PlayArrow as ExecuteIcon } from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import ApiService from '../services/api';

const AgentSelector: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState('');
  const [taskType, setTaskType] = useState('');
  const [taskData, setTaskData] = useState('{}');
  const [result, setResult] = useState<any>(null);

  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => ApiService.listAgents(),
  });

  const executeMutation = useMutation({
    mutationFn: (data: any) => ApiService.executeAgentTask(data.agentType, data.taskType, data.taskData),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleExecute = () => {
    try {
      const parsedData = JSON.parse(taskData);
      executeMutation.mutate({
        agentType: selectedAgent,
        taskType,
        taskData: parsedData,
      });
    } catch (error) {
      alert('Invalid JSON in task data');
    }
  };

  // Agent-specific task types
  const getTaskTypes = (agentType: string) => {
    const taskTypes: Record<string, string[]> = {
      report: ['generate_weekly_report', 'generate_meeting_minutes', 'generate_document'],
      monitoring: ['health_check', 'check_database', 'analyze_logs'],
      its: ['create_incident', 'create_change_request', 'update_cmdb'],
      db_extract: ['generate_sql', 'execute_query', 'validate_data'],
      change_mgmt: ['deploy_performance_improvement', 'emergency_patch', 'regular_change'],
      biz_support: ['answer_usage_question', 'find_contact', 'request_account'],
      sop: ['incident_detection_response', 'search_similar_incidents', 'incident_notification'],
      infra: ['analyze_performance', 'auto_scaling', 'automated_patching'],
    };
    return taskTypes[agentType] || [];
  };

  if (isLoading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Execute Agent Task
      </Typography>

      <Grid container spacing={3}>
        {/* Agent Selection */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Select Agent
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Agent</InputLabel>
                <Select
                  value={selectedAgent}
                  label="Agent"
                  onChange={(e) => {
                    setSelectedAgent(e.target.value);
                    setTaskType('');
                  }}
                >
                  {agents?.map((agent: any) => (
                    <MenuItem key={agent.type} value={agent.type}>
                      {agent.name} ({agent.type})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {selectedAgent && (
                <>
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Task Type</InputLabel>
                    <Select
                      value={taskType}
                      label="Task Type"
                      onChange={(e) => setTaskType(e.target.value)}
                    >
                      {getTaskTypes(selectedAgent).map((type) => (
                        <MenuItem key={type} value={type}>
                          {type}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    fullWidth
                    label="Task Data (JSON)"
                    multiline
                    rows={10}
                    value={taskData}
                    onChange={(e) => setTaskData(e.target.value)}
                    sx={{ mb: 2 }}
                  />

                  <Button
                    variant="contained"
                    fullWidth
                    startIcon={<ExecuteIcon />}
                    onClick={handleExecute}
                    disabled={!taskType || executeMutation.isPending}
                  >
                    {executeMutation.isPending ? 'Executing...' : 'Execute Task'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Result Display */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Execution Result
              </Typography>

              {executeMutation.isPending && (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              )}

              {executeMutation.isError && (
                <Alert severity="error">
                  Failed to execute task: {(executeMutation.error as any).message}
                </Alert>
              )}

              {result && (
                <Box>
                  <Alert severity={result.success ? 'success' : 'error'} sx={{ mb: 2 }}>
                    Task {result.success ? 'Completed' : 'Failed'}
                  </Alert>

                  <Typography variant="body2" gutterBottom>
                    <strong>Task ID:</strong> {result.task_id}
                  </Typography>

                  <Typography variant="body2" gutterBottom>
                    <strong>Agent:</strong> {result.agent_type}
                  </Typography>

                  <Box
                    sx={{
                      mt: 2,
                      p: 2,
                      bgcolor: 'grey.100',
                      borderRadius: 1,
                      maxHeight: 400,
                      overflow: 'auto',
                    }}
                  >
                    <Typography variant="caption" component="pre">
                      {JSON.stringify(result.result, null, 2)}
                    </Typography>
                  </Box>
                </Box>
              )}

              {!result && !executeMutation.isPending && (
                <Typography color="textSecondary" align="center" sx={{ p: 3 }}>
                  Execute a task to see results here
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AgentSelector;
