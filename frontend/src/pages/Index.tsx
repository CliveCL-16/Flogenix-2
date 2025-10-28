import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, User, Shield, ArrowRight } from "lucide-react";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/10">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-primary flex items-center justify-center shadow-lg">
              <Activity className="w-12 h-12 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-foreground mb-4">Flowgenix</h1>
          <p className="text-xl text-muted-foreground mb-2">Intelligent Healthcare Claims Processing</p>
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            Powered by Agentic AI for faster, more accurate healthcare claim decisions
          </p>
        </div>

        {/* Portal Selection */}
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-semibold text-center text-foreground mb-8">Choose Your Portal</h2>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* User Portal Card */}
            <Link to="/user">
              <Card className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer border-primary/20 hover:border-primary/40 bg-card group h-full">
                <div className="flex flex-col items-center text-center">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <User className="w-10 h-10 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold text-foreground mb-3">User Portal</h3>
                  <p className="text-muted-foreground mb-6">
                    For insurance holders to submit claims, track status, and manage their healthcare coverage
                  </p>
                  <ul className="space-y-2 mb-8 text-left w-full">
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-primary mr-2" />
                      Submit new claims
                    </li>
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-primary mr-2" />
                      Track claim status
                    </li>
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-primary mr-2" />
                      View coverage details
                    </li>
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-primary mr-2" />
                      Access claim history
                    </li>
                  </ul>
                  <Button className="w-full" size="lg">
                    Access User Portal
                  </Button>
                </div>
              </Card>
            </Link>

            {/* Admin Portal Card */}
            <Link to="/admin">
              <Card className="p-8 hover:shadow-xl transition-all duration-300 cursor-pointer border-primary/20 hover:border-primary/40 bg-card group h-full">
                <div className="flex flex-col items-center text-center">
                  <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-info/20 to-info/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Shield className="w-10 h-10 text-info" />
                  </div>
                  <h3 className="text-2xl font-bold text-foreground mb-3">Admin Portal</h3>
                  <p className="text-muted-foreground mb-6">
                    For claims processors to review submissions, utilize AI processing, and manage decisions
                  </p>
                  <ul className="space-y-2 mb-8 text-left w-full">
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-info mr-2" />
                      View all claims
                    </li>
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-info mr-2" />
                      AI-powered processing
                    </li>
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-info mr-2" />
                      Analytics & reporting
                    </li>
                    <li className="flex items-center text-sm text-foreground">
                      <ArrowRight className="w-4 h-4 text-info mr-2" />
                      Fraud detection
                    </li>
                  </ul>
                  <Button className="w-full bg-info hover:bg-info/90 text-info-foreground" size="lg">
                    Access Admin Portal
                  </Button>
                </div>
              </Card>
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-20 max-w-5xl mx-auto">
          <h3 className="text-2xl font-semibold text-center text-foreground mb-10">
            Why Choose Flowgenix?
          </h3>
          
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="p-6 bg-card border-primary/10">
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                <Activity className="w-6 h-6 text-primary" />
              </div>
              <h4 className="font-semibold text-foreground mb-2">AI-Powered Processing</h4>
              <p className="text-sm text-muted-foreground">
                Multi-agent AI system provides transparent reasoning and faster claim decisions
              </p>
            </Card>

            <Card className="p-6 bg-card border-primary/10">
              <div className="w-12 h-12 rounded-lg bg-success/10 flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-success" />
              </div>
              <h4 className="font-semibold text-foreground mb-2">Fraud Detection</h4>
              <p className="text-sm text-muted-foreground">
                Advanced algorithms automatically flag suspicious claims for review
              </p>
            </Card>

            <Card className="p-6 bg-card border-primary/10">
              <div className="w-12 h-12 rounded-lg bg-info/10 flex items-center justify-center mb-4">
                <ArrowRight className="w-6 h-6 text-info" />
              </div>
              <h4 className="font-semibold text-foreground mb-2">Real-Time Updates</h4>
              <p className="text-sm text-muted-foreground">
                Track your claims in real-time with instant notifications on status changes
              </p>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
