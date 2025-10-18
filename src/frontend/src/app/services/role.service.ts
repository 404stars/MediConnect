import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class RoleService {
  private apiUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getRoles(): Observable<any> {
    return this.http.get(`${this.apiUrl}/roles`);
  }

  createRole(role: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/create_role`, role);
  }

  assignRole(data: { user_id: number; role_name: string }): Observable<any> {
    return this.http.post(`${this.apiUrl}/assign_role`, data);
  }

  removeRole(data: { user_id: number; role_name: string }): Observable<any> {
    return this.http.delete(`${this.apiUrl}/remove_role`, { body: data });
  }

  initializeRoles(): Observable<any> {
    return this.http.post(`${this.apiUrl}/initialize_roles`, {});
  }
}
