export interface User {
  id: number;
  email: string | null;
  username: string | null;
  first_name: string;
  telegram_id: number | null;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Room {
  id: number;
  code: string;
  name: string | null;
  status: "active" | "closed" | "cancelled";
  owner_id: number;
  is_owner: boolean;
  members_count: number;
  created_at: string;
}

export interface Member {
  user_id: number;
  first_name: string;
  username: string | null;
  is_owner: boolean;
  joined_at: string;
}

export interface Payment {
  id: number;
  room_id: number;
  user_id: number;
  payer_name: string;
  amount: number;
  description: string | null;
  created_at: string;
}

export type SettlementStatus = "pending" | "confirmed";

export interface Settlement {
  id: number;
  room_id: number;
  from_user_id: number;
  to_user_id: number;
  amount: number;
  status: SettlementStatus;
  created_at: string;
  confirmed_at: string | null;
}

export interface Transfer {
  from_user_id: number;
  to_user_id: number;
  amount: number;
}

export interface Dashboard {
  balance: number;
  you_owe: number;
  you_are_owed: number;
  members_count: number;
  pending_settlements: number;
  recent_payments: Payment[];
  transfers: Transfer[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
