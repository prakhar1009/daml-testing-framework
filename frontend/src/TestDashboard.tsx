import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircleOutline as CheckCircleIcon,
  ErrorOutline as ErrorIcon,
  HourglassEmpty as HourglassEmptyIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';

// --- Type Definitions ---

type TestStatus = 'pass' | 'fail' | 'running';

interface TestResult {
  id: string;
  name: string;
  status: TestStatus;
  durationMs: number;
  error?: string;
}

interface TestSuite {
  id: string;
  name: string;
  tests: TestResult[];
  passCount: number;
  failCount: number;
  runningCount: number;
  totalCount: number;
  durationMs: number;
}

interface TestRun {
  id: string;
  timestamp: string; // ISO 8601 format
  commitHash: string;
  branch: string;
  suites: TestSuite[];
  overallPassRate: number;
  totalDurationMs: number;
  totalTests: number;
  status: 'completed' | 'in_progress';
}


// --- Mock Data Generation ---
// In a real application, this data would come from a backend API.

const generateMockTestResult = (suiteName: string, index: number): TestResult => {
  const statusRoll = Math.random();
  let status: TestStatus;
  if (statusRoll < 0.85) status = 'pass';
  else if (statusRoll < 0.98) status = 'fail';
  else status = 'running';

  return {
    id: `test-${suiteName}-${index}`,
    name: `should correctly ${['handle proposal', 'reject invalid input', 'calculate fees', 'transfer ownership', 'archive gracefully'][index % 5]}`,
    status,
    durationMs: Math.floor(Math.random() * 200) + 50,
    error: status === 'fail' ? `Assertion failed: expected ${Math.random() * 100} to equal ${Math.random() * 100}` : undefined,
  };
};

const generateMockTestSuite = (name: string): TestSuite => {
  const tests = Array.from({ length: Math.floor(Math.random() * 8) + 3 }, (_, i) => generateMockTestResult(name, i));
  const passCount = tests.filter(t => t.status === 'pass').length;
  const failCount = tests.filter(t => t.status === 'fail').length;
  const runningCount = tests.filter(t => t.status === 'running').length;
  return {
    id: `suite-${name}`,
    name,
    tests,
    passCount,
    failCount,
    runningCount,
    totalCount: tests.length,
    durationMs: tests.reduce((sum, t) => sum + t.durationMs, 0),
  };
};

const generateMockTestRun = (index: number, daysAgo: number): TestRun => {
  const suites = [
    generateMockTestSuite('Token.Transfer'),
    generateMockTestSuite('Token.DvP'),
    generateMockTestSuite('Roles.MasterAgreement'),
    generateMockTestSuite('Workflows.Issuance'),
  ];
  const totalTests = suites.reduce((sum, s) => sum + s.totalCount, 0);
  const totalPassed = suites.reduce((sum, s) => sum + s.passCount, 0);
  const timestamp = new Date();
  timestamp.setDate(timestamp.getDate() - daysAgo);

  return {
    id: `run-${index}`,
    timestamp: timestamp.toISOString(),
    commitHash: `a1b2c3d${index}`,
    branch: index % 3 === 0 ? 'main' : 'feature/new-logic',
    suites,
    overallPassRate: totalTests > 0 ? (totalPassed / totalTests) * 100 : 100,
    totalDurationMs: suites.reduce((sum, s) => sum + s.durationMs, 0),
    totalTests,
    status: daysAgo === 0 && Math.random() > 0.8 ? 'in_progress' : 'completed',
  };
};

const MOCK_TEST_RUNS: TestRun[] = Array.from({ length: 10 }, (_, i) => generateMockTestRun(10 - i, i)).reverse();


// --- Helper Components ---

const StatusIcon: React.FC<{ status: TestStatus }> = ({ status }) => {
  switch (status) {
    case 'pass':
      return <CheckCircleIcon color="success" />;
    case 'fail':
      return <ErrorIcon color="error" />;
    case 'running':
      return <HourglassEmptyIcon color="warning" />;
    default:
      return null;
  }
};

const PassRateProgress: React.FC<{ value: number }> = ({ value }) => {
  const color = value > 90 ? 'success' : value > 70 ? 'warning' : 'error';
  return <LinearProgress variant="determinate" value={value} color={color} sx={{ height: 8, borderRadius: 4 }} />;
};


// --- Main Dashboard Component ---

const TestDashboard: React.FC = () => {
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate API call
    const fetchTestRuns = async () => {
      try {
        setLoading(true);
        // Replace with actual fetch call:
        // const response = await fetch('/api/test-runs');
        // const data = await response.json();
        // setTestRuns(data);
        await new Promise(resolve => setTimeout(resolve, 1000));
        setTestRuns(MOCK_TEST_RUNS);
      } catch (e) {
        setError('Failed to fetch test run data.');
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    fetchTestRuns();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading Test Data...</Typography>
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (testRuns.length === 0) {
    return <Alert severity="info">No test runs found.</Alert>;
  }

  const latestRun = testRuns[testRuns.length - 1];

  const chartData = testRuns.map(run => ({
    name: format(parseISO(run.timestamp), 'MMM d, HH:mm'),
    passRate: run.overallPassRate.toFixed(2),
  }));

  const formatDuration = (ms: number) => `${(ms / 1000).toFixed(2)}s`;

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom component="h1">
        Daml Test Framework Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Latest Run Summary */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Latest Run Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography color="text.secondary">Timestamp</Typography>
                  <Typography variant="h6">{format(parseISO(latestRun.timestamp), 'yyyy-MM-dd HH:mm:ss')}</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography color="text.secondary">Branch / Commit</Typography>
                  <Typography variant="h6" noWrap>{latestRun.branch} ({latestRun.commitHash.substring(0, 7)})</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography color="text.secondary">Total Duration</Typography>
                  <Typography variant="h6">{formatDuration(latestRun.totalDurationMs)}</Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography color="text.secondary">Overall Pass Rate</Typography>
                  <Typography variant="h6" color={latestRun.overallPassRate > 90 ? 'success.main' : 'error.main'}>
                    {latestRun.overallPassRate.toFixed(2)}%
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Historical Trend */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" component="h3" gutterBottom>
              Pass Rate History
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} unit="%" />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="passRate" stroke="#8884d8" activeDot={{ r: 8 }} name="Overall Pass Rate (%)" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Test Suites from Latest Run */}
        <Grid item xs={12}>
          <Typography variant="h5" component="h2" gutterBottom sx={{ mt: 2 }}>
            Test Suites
          </Typography>
          {latestRun.suites.map((suite) => {
            const suitePassRate = suite.totalCount > 0 ? (suite.passCount / suite.totalCount) * 100 : 100;
            return (
              <Accordion key={suite.id}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Grid container alignItems="center" spacing={2}>
                    <Grid item xs={12} md={5}>
                      <Typography>{suite.name}</Typography>
                    </Grid>
                    <Grid item xs={6} md={2}>
                        <Chip label={`${suite.passCount} / ${suite.totalCount} passed`} color={suite.failCount === 0 ? "success" : "error"} size="small" />
                    </Grid>
                    <Grid item xs={6} md={2}>
                      <Typography variant="body2" color="text.secondary">
                        {formatDuration(suite.durationMs)}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={3}>
                       <PassRateProgress value={suitePassRate} />
                    </Grid>
                  </Grid>
                </AccordionSummary>
                <AccordionDetails>
                  <List dense>
                    {suite.tests.map((test) => (
                      <ListItem key={test.id} disablePadding>
                        <ListItemIcon>
                          <StatusIcon status={test.status} />
                        </ListItemIcon>
                        <ListItemText
                          primary={test.name}
                          secondary={test.error || `Duration: ${test.durationMs}ms`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Grid>
      </Grid>
    </Container>
  );
};

export default TestDashboard;