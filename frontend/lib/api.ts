import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export const api = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: {
        "Content-Type": "application/json",
    },
});

// Types
export interface Filing {
    id: number;
    title: string;
    filing_type: string;
    source: string;
    status: string;
    country: string;
    region: string;
    filed_at: string;
    url: string | null;
    description: string | null;
    cik: string | null;
    accession_number: string | null;
    company_name: string | null;
    ticker: string | null;
    period_of_report: string | null;
    is_amendment: boolean;
    items: string[] | null;
    created_at: string;
    updated_at: string;
}

export interface Bill {
    id: number;
    bill_number: string;
    bill_type: string;
    congress_number: number;
    title: string;
    short_title: string | null;
    summary: string | null;
    url: string | null;
    status: string;
    chamber: string;
    policy_area: string;
    country: string;
    region: string;
    introduced_at: string;
    last_action_at: string | null;
    sponsor_name: string | null;
    sponsor_party: string | null;
    sponsor_state: string | null;
    cosponsors_count: number;
    affected_sectors: string[] | null;
    affected_tickers: string[] | null;
    market_sentiment: string | null;
    created_at: string;
    updated_at: string;
}

export interface Contract {
    id: number;
    award_id: string;
    award_type: string;
    description: string;
    total_amount: number;
    base_amount: number;
    potential_amount: number | null;
    start_date: string;
    end_date: string | null;
    signed_date: string | null;
    agency_id: string;
    agency_name: string;
    sub_agency_name: string | null;
    recipient_id: string;
    recipient_name: string;
    ticker: string | null;
    recipient_country: string;
    recipient_state: string | null;
    naics_code: string | null;
    naics_description: string | null;
    psc_code: string | null;
    is_compete: boolean;
    country: string;
    region: string;
    url: string | null;
    created_at: string;
    updated_at: string;
}

export interface Lobbying {
    id: number;
    filing_id: string;
    client_name: string;
    lobbyist_firm: string | null;
    amount: number | null;
    year: number | null;
    quarter: number | null;
    issues: string[] | null;
    ticker: string | null;
    country: string;
    region: string;
    url: string | null;
    created_at: string;
    updated_at: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
}

// API functions
export const getFilings = async (params?: {
    filing_type?: string;
    country?: string;
    ticker?: string;
    company_name?: string;
    page?: number;
    page_size?: number;
}): Promise<PaginatedResponse<Filing>> => {
    const { data } = await api.get("/filings/", { params });
    return data;
};

export const getBills = async (params?: {
    status?: string;
    chamber?: string;
    policy_area?: string;
    sponsor_party?: string;
    page?: number;
    page_size?: number;
}): Promise<PaginatedResponse<Bill>> => {
    const { data } = await api.get("/bills/", { params });
    return data;
};

export const getContracts = async (params?: {
    agency_name?: string;
    ticker?: string;
    min_amount?: number;
    page?: number;
    page_size?: number;
}): Promise<PaginatedResponse<Contract>> => {
    const { data } = await api.get("/contracts/", { params });
    return data;
};

export const getLobbying = async (params?: {
    client_name?: string;
    lobbyist_firm?: string;
    ticker?: string;
    year?: number;
    page?: number;
    page_size?: number;
}): Promise<PaginatedResponse<Lobbying>> => {
    const { data } = await api.get("/lobbying/", { params });
    return data;
};