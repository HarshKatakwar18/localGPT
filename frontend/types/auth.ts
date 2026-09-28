export type User = {
  id: string;
  name: string;
  email: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
};

export type RegisterRequest = {
  name: string;
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};