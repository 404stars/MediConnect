import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ReprogramarCitaRequest {
  id_nuevo_bloque: number;
  id_motivo_cancelacion: number;
  observaciones?: string;
}

export interface Especialidad {
  id_especialidad: number;
  nombre: string;
  descripcion?: string;
}

export interface Profesional {
  id_profesional: number;
  nombre_completo: string;
  registro_profesional: string;
  especialidades: string[];
}

export interface BloqueDisponible {
  id_bloque: number;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  profesional: string;
  especialidad: string;
}

export interface CitaPaciente {
  id_cita: number;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  estado: string;
  profesional: string;
  especialidad: string;
  motivo_consulta?: string;
  observaciones?: string;
}

export interface SolicitarCitaRequest {
  id_bloque: number;
  motivo_consulta?: string;
}

export interface CancelarCitaRequest {
  id_motivo_cancelacion: number;
  observaciones?: string;
}

export interface MotivoCancelacion {
  id_motivo: number;
  descripcion: string;
}

@Injectable({
  providedIn: 'root'
})
export class PacientesService {
  private apiUrl = 'http://127.0.0.1:8000/pacientes';

  constructor(private http: HttpClient) {}

  getEspecialidades(): Observable<Especialidad[]> {
    return this.http.get<Especialidad[]>(`${this.apiUrl}/especialidades`);
  }

  getMotivosCancelacion(): Observable<MotivoCancelacion[]> {
    return this.http.get<MotivoCancelacion[]>(`${this.apiUrl}/motivos-cancelacion`);
  }

  getProfesionales(idEspecialidad?: number): Observable<Profesional[]> {
    let url = `${this.apiUrl}/profesionales`;
    if (idEspecialidad) {
      url += `?id_especialidad=${idEspecialidad}`;
    }
    return this.http.get<Profesional[]>(url);
  }

  getBloquesDisponibles(params: {
    id_profesional?: number;
    id_especialidad?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  } = {}): Observable<BloqueDisponible[]> {
    let url = `${this.apiUrl}/bloques-disponibles`;
    const queryParams = new URLSearchParams();

    if (params.id_profesional) {
      queryParams.append('id_profesional', params.id_profesional.toString());
    }
    if (params.id_especialidad) {
      queryParams.append('id_especialidad', params.id_especialidad.toString());
    }
    if (params.fecha_desde) {
      queryParams.append('fecha_desde', params.fecha_desde);
    }
    if (params.fecha_hasta) {
      queryParams.append('fecha_hasta', params.fecha_hasta);
    }

    if (queryParams.toString()) {
      url += `?${queryParams.toString()}`;
    }

    return this.http.get<BloqueDisponible[]>(url);
  }

  solicitarCita(request: SolicitarCitaRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/solicitar-cita`, request);
  }

  getMisCitas(estado?: string): Observable<CitaPaciente[]> {
    let url = `${this.apiUrl}/mis-citas`;
    if (estado) {
      url += `?estado=${estado}`;
    }
    console.log('📡 Haciendo petición a:', url);
    return this.http.get<CitaPaciente[]>(url);
  }

  cancelarCita(idCita: number, request: CancelarCitaRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/cancelar-cita/${idCita}`, request);
  }

  reprogramarCita(idCita: number, request: ReprogramarCitaRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/reprogramar-cita/${idCita}`, request);
  }
}
