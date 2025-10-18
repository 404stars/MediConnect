import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserRole {
  id_rol: number;
  nombre: string;
}

export interface AdminUser {
  id_usuario: number;
  rut: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  email: string;
  telefono?: string;
  roles: UserRole[];
}

export interface Role {
  id_rol: number;
  nombre: string;
  descripcion?: string;
}

export interface CreateUserData {
  rut: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  email: string;
  telefono?: string;
  password: string;
  roles: number[];
}

export interface UsersListResponse {
  users: AdminUser[];
  total: number;
}

export interface RolesListResponse {
  roles: Role[];
}

export interface CitaAdmin {
  id_cita: number;
  fecha: string;
  hora: string;
  estado: string;
  observaciones?: string;
  created_at: string;
  updated_at?: string;
  paciente: {
    id: number;
    nombres: string;
    apellidos: string;
    rut: string;
    email: string;
    telefono?: string;
    fecha_nacimiento?: string;
  };
  profesional: {
    id: number;
    nombres: string;
    apellidos: string;
    especialidad: {
      id: number;
      nombre: string;
      descripcion?: string;
    };
  };
  motivo_cancelacion?: {
    id: number;
    descripcion: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private apiUrl = 'http://127.0.0.1:8000/admin';

  constructor(private http: HttpClient) {}

  getUsers(skip: number = 0, limit: number = 100): Observable<UsersListResponse> {
    return this.http.get<UsersListResponse>(`${this.apiUrl}/users?skip=${skip}&limit=${limit}`);
  }

  getRoles(): Observable<RolesListResponse> {
    return this.http.get<RolesListResponse>(`${this.apiUrl}/roles`);
  }

  createUser(userData: CreateUserData): Observable<any> {
    const userDataToSend = {
      ...userData,
      apellido_materno: userData.apellido_materno?.trim() || null,
      telefono: userData.telefono?.trim() || null
    };
    
    return this.http.post(`${this.apiUrl}/users`, userDataToSend);
  }

  updateUserRoles(userId: number, roles: number[]): Observable<any> {
    return this.http.put(`${this.apiUrl}/users/${userId}/roles`, {
      user_id: userId,
      roles: roles
    });
  }

  deleteUser(userId: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/users/${userId}`);
  }

  getTodasLasCitas(params: any = {}): Observable<CitaAdmin[]> {
    const queryParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        queryParams.append(key, params[key].toString());
      }
    });

    const url = `http://127.0.0.1:8000/pacientes/admin/todas-las-citas${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get<CitaAdmin[]>(url);
  }

  getEspecialidades(): Observable<{id_especialidad: number, nombre: string}[]> {
    return this.http.get<{id_especialidad: number, nombre: string}[]>(`${this.apiUrl}/especialidades`);
  }

  exportarReporteCitas(params: any = {}): Observable<Blob> {
    const queryParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        queryParams.append(key, params[key].toString());
      }
    });

    const url = `${this.apiUrl}/reportes/citas-csv${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get(url, { responseType: 'blob' });
  }

  getEstadisticasUtilizacion(params: any = {}): Observable<any> {
    const queryParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        queryParams.append(key, params[key].toString());
      }
    });

    const url = `${this.apiUrl}/reportes/estadisticas-utilizacion${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get(url);
  }

  exportarPacientesAtendidos(params: any = {}): Observable<Blob> {
    const queryParams = new URLSearchParams();
    
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
        queryParams.append(key, params[key].toString());
      }
    });

    const url = `${this.apiUrl}/reportes/pacientes-atendidos-csv${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    return this.http.get(url, { responseType: 'blob' });
  }

  marcarCitaAtendida(citaId: number): Observable<any> {
    return this.http.put(`http://127.0.0.1:8000/pacientes/admin/marcar-atendida/${citaId}`, {});
  }

  marcarCitaNoAsistio(citaId: number): Observable<any> {
    return this.http.put(`http://127.0.0.1:8000/pacientes/admin/marcar-no-asistio/${citaId}`, {});
  }
}
