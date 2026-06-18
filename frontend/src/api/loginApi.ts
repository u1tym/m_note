import axios from 'axios'

import { loginOrigin } from '../config'

export interface MeResponse {
  user: {
    id: number
    username: string
  }
}

export async function fetchMe(): Promise<MeResponse> {
  const { data } = await axios.get<MeResponse>(`${loginOrigin}/me`, {
    withCredentials: true,
  })
  return data
}

export async function postRefresh(): Promise<void> {
  await axios.post(`${loginOrigin}/refresh`, {}, { withCredentials: true })
}

export async function postLogin(username: string, password: string): Promise<void> {
  await axios.post(
    `${loginOrigin}/login`,
    { username, password },
    { withCredentials: true },
  )
}
