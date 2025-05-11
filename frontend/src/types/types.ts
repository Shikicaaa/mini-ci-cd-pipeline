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

  export interface ConfigResponse{
    data: {
        main_branch: string;
        repo_url: string;
        id: number;
        docker_username: string;
    };
    message: string;
  }
  
  export interface PipelineResponse{
    data: {
        id: number;
        status: string;
        trigger_time: Date;
        end_time: Date;
        commit_sha: string;
        trigger_event_id: string;
        logs: string;
        config_id: number;
    };
    message: string;
  }