import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Activity, AlertCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Alert, AlertDescription } from "@/components/ui/alert";

const Login = () => {
  const [searchParams] = useSearchParams();
  const type = (searchParams.get('type') as 'user' | 'admin') || 'user';
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    const success = login(email, password, type);
    if (success) {
      navigate(type === 'admin' ? '/admin' : '/user');
    } else {
      setError("Invalid credentials. Please try again.");
    }
  };

  const demoCredentials = type === 'admin' 
    ? { email: 'admin@demo.com', password: 'admin123' }
    : { email: 'user@demo.com', password: 'user123' };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-primary flex items-center justify-center mb-4">
            <Activity className="w-10 h-10 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground mb-2">Flowgenix</h1>
          <p className="text-muted-foreground text-center">
            {type === 'admin' ? 'Admin Portal Login' : 'User Portal Login'}
          </p>
        </div>

        <Alert className="mb-6 bg-info/10 border-info/20">
          <AlertCircle className="h-4 w-4 text-info" />
          <AlertDescription className="text-sm text-foreground">
            <strong>Demo Credentials:</strong><br />
            Email: {demoCredentials.email}<br />
            Password: {demoCredentials.password}
          </AlertDescription>
        </Alert>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button type="submit" className="w-full">
            Sign In
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => navigate('/')}
          >
            Back to Home
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Login;
