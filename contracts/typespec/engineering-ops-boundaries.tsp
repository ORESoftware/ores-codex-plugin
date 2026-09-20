namespace Ores.CodexPlugin;

model GitHubBoundary {
  owners: string[];
  logins: string[];
  secondaryLogins: string[];
}

model LinearBoundary {
  userEmail: string;
  workspaceName: string;
  workspaceUrl: string;
  mcpUrl: string;
}

model SlackBoundary {
  domain: string;
  teamId: string;
}

model AppBindings {
  github: string;
  linear: string;
  slack: string;
}

model EngineeringOpsBoundaries {
  github: GitHubBoundary;
  linear: LinearBoundary;
  slack: SlackBoundary;
  apps: AppBindings;
}
