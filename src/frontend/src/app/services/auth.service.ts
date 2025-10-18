import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap, catchError, switchMap, map } from 'rxjs/operators';
import { of } from 'rxjs';

interface User {
  id: number;
  nombre: string;
  email: string;
  rut: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface UserWithRoles extends User {
  roles: string[];
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private apiUrl = 'http://127.0.0.1:8000';
  private tokenKey = 'auth_token';
  private userKey = 'auth_user';
  private activeRoleKey = 'active_role';
  private currentUserSubject = new BehaviorSubject<UserWithRoles | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient) {
    this.initializeAuth();
  }

  private initializeAuth(): void {
    const token = this.getToken();
    const savedUser = this.getSavedUser();
    
    if (token && savedUser) {
      this.currentUserSubject.next(savedUser);
            this.validateToken();
    }
  }

  register(user: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/register`, user);
  }

  login(credentials: any): Observable<LoginResponse> {
  return this.http.post<LoginResponse>(`${this.apiUrl}/auth/login`, credentials).pipe(
      switchMap((response: LoginResponse) => {
        if (response.access_token) {
          this.setToken(response.access_token);
          this.saveUser(response.user);
          
          const userWithEmptyRoles: UserWithRoles = {
            ...response.user,
            roles: []
          };
          this.currentUserSubject.next(userWithEmptyRoles);
          
          return this.loadUserRoles().pipe(
            switchMap(() => this.getUserAdditionalInfo()),
            tap((info) => {
              if (info) {
                this.saveAdditionalInfo(info);
              }
            }),
            map(() => response), 
            catchError(() => of(response)) 
          );
        }
        return of(response);
      })
    );
  }

  logout(): Observable<any> {
    const token = this.getToken();
    if (!token) {
      this.clearAuthData();
      return of({ message: 'No hay sesión activa' });
    }

    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    
    return this.http.post(`${this.apiUrl}/auth/logout`, {}, { headers }).pipe(
      tap(() => {
        this.clearAuthData();
      }),
      catchError((error) => {
                this.clearAuthData();
        return of({ message: 'Sesión cerrada localmente' });
      })
    );
  }

  private clearAuthData(): void {
    this.removeToken();
    this.removeSavedUser();
    this.removeActiveRole();
    this.clearAdditionalInfo();
    this.currentUserSubject.next(null);
  }
  
  setActiveRole(role: string): void {
    localStorage.setItem(this.activeRoleKey, role);
  }
  
  getActiveRole(): string | null {
    return localStorage.getItem(this.activeRoleKey);
  }
  
  removeActiveRole(): void {
    localStorage.removeItem(this.activeRoleKey);
  }
  
  hasActiveRole(role: string): boolean {
    const activeRole = this.getActiveRole();
    return activeRole === role;
  }
  
  canAccessView(allowedRoles: string[]): boolean {
    const activeRole = this.getActiveRole();
    return activeRole ? allowedRoles.includes(activeRole) : false;
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  private setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  private removeToken(): void {
    localStorage.removeItem(this.tokenKey);
  }

  private saveUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  private getSavedUser(): UserWithRoles | null {
    const savedUser = localStorage.getItem(this.userKey);
    if (savedUser) {
      try {
        return JSON.parse(savedUser);
      } catch {
        this.removeSavedUser();
        return null;
      }
    }
    return null;
  }

  private removeSavedUser(): void {
    localStorage.removeItem(this.userKey);
  }

  isLoggedIn(): boolean {
    return !!this.getToken() && !!this.currentUserSubject.value;
  }

  private validateToken(): void {
    this.loadUserRoles().subscribe({
      error: () => {
        this.clearAuthData();
      }
    });
  }

  private loadUserRoles(): Observable<any> {
    const token = this.getToken();
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    
    console.log('Cargando roles del usuario con token:', token ? 'Token presente' : 'No token');
    console.log('Usuario actual antes de cargar roles:', this.currentUserSubject.value);
    
    return this.http.get(`${this.apiUrl}/auth/me/roles`, { headers }).pipe(
      tap((response: any) => {
        console.log('Respuesta de roles:', response);
        const currentUser = this.currentUserSubject.value;
        console.log('Usuario actual al procesar roles:', currentUser);
        if (currentUser) {
          const userWithRoles: UserWithRoles = {
            ...currentUser,
            roles: response.roles || []
          };
          console.log('Usuario con roles actualizado:', userWithRoles);
          this.currentUserSubject.next(userWithRoles);
          this.saveUser(userWithRoles);
        } else {
          console.error('No hay usuario actual para actualizar con roles');
        }
      }),
      catchError((error) => {
        console.error('Error cargando roles:', error);
        if (error.status === 401) {
          this.clearAuthData();
        }
        throw error;
      })
    );
  }

  getCurrentUser(): UserWithRoles | null {
    return this.currentUserSubject.value;
  }

  getCurrentUserRoles(): string[] {
    const user = this.currentUserSubject.value;
    return user ? user.roles : [];
  }

  hasRole(role: string): boolean {
    return this.getCurrentUserRoles().includes(role);
  }

  hasPermission(permission: string): boolean {
    const roles = this.getCurrentUserRoles();
    const permissions: { [key: string]: string[] } = {
      'view_own_profile': ['Paciente', 'Médico', 'Recepcionista', 'Administrador'],
      'manage_users': ['Administrador'],
      'manage_roles': ['Administrador'],
      'view_all_data': ['Administrador'],
      'manage_appointments': ['Médico', 'Recepcionista', 'Administrador'],
      'view_patients': ['Médico', 'Recepcionista', 'Administrador'],
      'book_appointment': ['Paciente'],
      'view_own_appointments': ['Paciente']
    };
    return roles.some(role => permissions[permission]?.includes(role));
  }

  getUserAdditionalInfo(): Observable<any> {
    const token = this.getToken();
    if (!token) {
      return of(null);
    }
    const headers = new HttpHeaders().set('Authorization', `Bearer ${token}`);
    return this.http.get(`${this.apiUrl}/auth/me/info-adicional`, { headers });
  }

  saveAdditionalInfo(info: any): void {
    localStorage.setItem('user_additional_info', JSON.stringify(info));
  }

  getAdditionalInfo(): any {
    const info = localStorage.getItem('user_additional_info');
    return info ? JSON.parse(info) : null;
  }

  clearAdditionalInfo(): void {
    localStorage.removeItem('user_additional_info');
  }
}