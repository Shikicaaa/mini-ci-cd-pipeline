export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  data: {
    message: string;
  };
  message: string;
}

export interface ConfigResponse {
  main_branch: string;
  repo_url: string;
  id: number;
  docker_username: string;
  SSH_host: string;
  SSH_port: string;
  SSH_username: string;
  SSH_key_path: string;
  SSH_key_passphrase: string;
  SSH_for_deploy: boolean;
}

export interface PipelineResponse {
    id: number;
    status: string;
    trigger_time: Date;
    end_time: Date;
    commit_sha: string;
    trigger_event_id: string;
    logs: string;
    config_id: number;
    logsExpanded: boolean;
}

export interface Config {
  main_branch: string;
  repo_url: string;
  id: number;
  docker_username: string;
  SSH_host: string;
  SSH_port: string;
  SSH_username: string;
  SSH_key_path: string;
  SSH_key_passphrase: string;
  SSH_for_deploy: boolean;
}

export interface BackendPayload {
  repo_url: string;
  main_branch: string;
  docker_username?: string | null;
  SSH_host?: string | null;
  SSH_port?: number | null;
  SSH_username?: string | null;
  SSH_key_path?: string | null;
  SSH_key_passphrase?: string | null;
  SSH_for_deploy: boolean;
}
export interface FormDataShape {
  repo_url?: string;
  main_branch?: string;
  docker_username?: string;
  SSH_host?: string;
  SSH_port?: number | null;
  SSH_username?: string;
  SSH_key_path?: string;
  SSH_key_passphrase?: string;
  SSH_for_deploy?: boolean;
}

export interface PipelineRun{ 
  id: number;
  status: string;
  trigger_time: Date;
  end_time: Date;
  commit_sha: string;
  trigger_event_id: string;
  logs: string;
  config_id: number;
  logsExpanded?: boolean;
}

export interface Webhook{
  id: number;
  repo_id: number;
  user_id: number;
  repo_url: string;
  url: string;
  secret: string;
}