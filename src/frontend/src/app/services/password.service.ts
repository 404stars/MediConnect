import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class PasswordService {
  private apiUrl = 'http://127.0.0.1:8000/auth';

  solicitarRecuperacion(email: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/recuperar-password`, { email });
  }

  restablecerPassword(token: string, nuevaPassword: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/restablecer-password`, {
      token: token,
      nueva_password: nuevaPassword
    });
  }

  constructor(private http: HttpClient) {}
}
