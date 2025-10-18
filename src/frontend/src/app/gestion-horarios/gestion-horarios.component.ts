import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Navbar } from '../shared/navbar/navbar';

interface Especialidad {
  id_especialidad: number;
  nombre: string;
  descripcion?: string;
}

interface EspecialidadConRelacion {
  id_especialidad: number;
  nombre: string;
  descripcion?: string;
  es_principal?: boolean;
}

interface MedicoResponse {
  id_profesional: number;
  id_usuario: number;
  nombre_completo: string;
  rut: string;
  registro_profesional: string;
  especialidades: EspecialidadConRelacion[];
}

interface BloqueHora {
  inicio: string; 
  fin: string;    
}

interface AgendaDiariaRequest {
  id_profesional: number;
  fecha: string; 
  hora_inicio: string; 
  hora_fin: string;    
  duracion_cita: number; 
  observaciones?: string;
  bloques?: BloqueHora[]; 
}

interface AgendaResponse {
  id_agenda: number;
  id_profesional: number;
  nombre_medico: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  duracion_cita: number;
  activa: boolean;
  observaciones?: string;
  bloques: {
    id_bloque: number;
    inicio: string;
    fin: string;
    disponible: boolean;
  }[];
}

@Component({
  selector: 'app-gestion-horarios',
  standalone: true,
  imports: [CommonModule, FormsModule, Navbar],
  template: `
    <app-navbar></app-navbar>
    <div class="container-fluid fondo-horarios">
      <div class="row justify-content-center">
        <div class="col-12 col-lg-10">
          <div class="card card-horarios sombra mt-4">
            <div class="card-header bg-azul text-white">
              <h3 class="mb-0">
                <i class="fas fa-calendar-alt me-2"></i>
                Gestión de Horarios Médicos
              </h3>
            </div>
            
            <div class="card-body">
              <ul class="nav nav-tabs mb-4" id="horariosTab" role="tablist">
                <li class="nav-item" role="presentation">
                  <button class="nav-link active" id="crear-agenda-tab" data-bs-toggle="tab" 
                          data-bs-target="#crear-agenda" type="button" role="tab">
                    <i class="fas fa-plus me-1"></i>Crear Agenda
                  </button>
                </li>
                <li class="nav-item" role="presentation">
                  <button class="nav-link" id="ver-agendas-tab" data-bs-toggle="tab" 
                          data-bs-target="#ver-agendas" type="button" role="tab">
                    <i class="fas fa-eye me-1"></i>Ver Agendas
                  </button>
                </li>
                <li class="nav-item" role="presentation">
                  <button class="nav-link" id="especialidades-tab" data-bs-toggle="tab" 
                          data-bs-target="#especialidades" type="button" role="tab">
                    <i class="fas fa-stethoscope me-1"></i>Especialidades
                  </button>
                </li>
              </ul>

              <div class="tab-content" id="horariosTabContent">
                <div class="tab-pane fade show active" id="crear-agenda" role="tabpanel">
                  <div class="row">
                    <div class="col-md-6">
                      <h5 class="mb-3">Nueva Agenda Diaria</h5>
                      
                      <form (ngSubmit)="crearAgenda()" #agendaForm="ngForm">
                        <div class="mb-3">
                          <label class="form-label">Médico:</label>
                          <select class="form-select campo" [(ngModel)]="nuevaAgenda.id_profesional" 
                                  name="medico" required>
                            <option value="">Seleccione un médico</option>
                            <option *ngFor="let medico of medicos" [value]="medico.id_profesional">
                              {{medico.nombre_completo}} - {{medico.rut}}
                            </option>
                          </select>
                        </div>

                        <div class="mb-3">
                          <label class="form-label">Fecha:</label>
                          <input type="date" class="form-control campo" 
                                 [(ngModel)]="nuevaAgenda.fecha" name="fecha" 
                                 [min]="fechaMinima" required>
                        </div>

                        <div class="row mb-3">
                          <div class="col-md-6">
                            <label class="form-label">Hora inicio (formato 24 hrs):</label>
                            <input type="time" class="form-control campo" 
                                   [(ngModel)]="nuevaAgenda.hora_inicio" name="hora_inicio" 
                                   step="60" pattern="[0-9]{2}:[0-9]{2}" placeholder="HH:MM"
                                   required>
                          </div>
                          <div class="col-md-6">
                            <label class="form-label">Hora fin (formato 24 hrs):</label>
                            <input type="time" class="form-control campo" 
                                   [(ngModel)]="nuevaAgenda.hora_fin" name="hora_fin" 
                                   step="60" pattern="[0-9]{2}:[0-9]{2}" placeholder="HH:MM"
                                   required>
                          </div>
                        </div>

                        <div class="mb-3">
                          <label class="form-label">Duración por cita (minutos):</label>
                          <input type="number" class="form-control campo" 
                                 [(ngModel)]="nuevaAgenda.duracion_cita" name="duracion_cita" 
                                 min="15" max="120" step="15" required>
                        </div>

                        <div class="mb-3">
                          <label class="form-label">Observaciones:</label>
                          <textarea class="form-control campo" 
                                    [(ngModel)]="nuevaAgenda.observaciones" name="observaciones" 
                                    placeholder="Observaciones adicionales..."></textarea>
                        </div>

                        <div class="d-flex justify-content-between align-items-center mb-3">
                          <h6>Bloques de Horario</h6>
                          <div>
                            <button type="button" class="btn btn-info btn-sm me-2" 
                                    (click)="generarBloquesAutomaticos()">
                              <i class="fas fa-magic"></i> Auto-generar
                            </button>
                            <button type="button" class="btn btn-success btn-sm" 
                                    (click)="agregarBloque()">
                              <i class="fas fa-plus"></i> Agregar Manual
                            </button>
                          </div>
                        </div>

                        <div class="alert alert-info" *ngIf="nuevaAgenda.bloques && nuevaAgenda.bloques.length === 0">
                          <small>
                            <i class="fas fa-lightbulb"></i>
                            <strong>Tip:</strong> Puedes usar "Auto-generar" para crear bloques automáticamente 
                            basado en tu horario de trabajo, o agregar bloques manualmente para horarios personalizados.
                          </small>
                        </div>

                        <div class="mb-3" *ngFor="let bloque of nuevaAgenda.bloques; let i = index">
                          <div class="row g-2 mb-2 p-2 border rounded">
                            <div class="col-md-4">
                              <label class="form-label small">Hora Inicio (24 hrs):</label>
                              <input type="time" class="form-control form-control-sm campo" 
                                     [(ngModel)]="bloque.inicio" [name]="'inicio_' + i" 
                                     step="60" pattern="[0-9]{2}:[0-9]{2}" placeholder="HH:MM"
                                     required>
                            </div>
                            <div class="col-md-4">
                              <label class="form-label small">Hora Fin (24 hrs):</label>
                              <input type="time" class="form-control form-control-sm campo" 
                                     [(ngModel)]="bloque.fin" [name]="'fin_' + i" 
                                     step="60" pattern="[0-9]{2}:[0-9]{2}" placeholder="HH:MM"
                                     required>
                            </div>
                            <div class="col-md-4 d-flex align-items-end">
                              <button type="button" class="btn btn-danger btn-sm" 
                                      (click)="eliminarBloque(i)">
                                <i class="fas fa-trash"></i>
                              </button>
                            </div>
                          </div>
                        </div>

                        <div class="d-flex gap-2">
                          <button type="submit" class="btn btn-primary" [disabled]="!agendaForm.valid || cargando">
                            <i class="fas fa-save me-1"></i>
                            <span *ngIf="!cargando">Crear Agenda</span>
                            <span *ngIf="cargando">Creando...</span>
                          </button>
                          <button type="button" class="btn btn-secondary" (click)="limpiarFormulario()">
                            <i class="fas fa-eraser me-1"></i>Limpiar
                          </button>
                        </div>
                      </form>
                    </div>

                    <div class="col-md-6">
                      <h6>Vista Previa</h6>
                      <div class="border rounded p-3 bg-light" style="min-height: 200px;">
                        <div *ngIf="nuevaAgenda.id_profesional">
                          <strong>Médico:</strong> {{getMedicoNombre(nuevaAgenda.id_profesional)}}<br>
                          <strong>Fecha:</strong> {{nuevaAgenda.fecha | date:'dd/MM/yyyy'}}<br>
                          <strong>Horario:</strong> {{nuevaAgenda.hora_inicio}} - {{nuevaAgenda.hora_fin}}<br>
                          <strong>Duración citas:</strong> {{nuevaAgenda.duracion_cita}} minutos<br>
                          <strong>Observaciones:</strong> {{nuevaAgenda.observaciones || 'Ninguna'}}<br><br>
                          
                          <strong>Horarios:</strong>
                          <div *ngIf="!nuevaAgenda.bloques || nuevaAgenda.bloques.length === 0" class="text-muted">
                            Se generarán automáticamente {{calcularBloquesAutomaticos()}} bloques
                          </div>
                          <div *ngFor="let bloque of nuevaAgenda.bloques" class="d-flex justify-content-between border-bottom py-1">
                            <span>{{bloque.inicio}} - {{bloque.fin}}</span>
                            <span class="text-success">Disponible</span>
                          </div>
                        </div>
                        <div *ngIf="!nuevaAgenda.id_profesional" class="text-muted">
                          Seleccione un médico para ver la vista previa
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="tab-pane fade" id="ver-agendas" role="tabpanel">
                  <div class="row mb-3">
                    <div class="col-md-4">
                      <label class="form-label">Médico:</label>
                      <select class="form-select campo" [(ngModel)]="filtroMedico">
                        <option value="">Todos los médicos</option>
                        <option *ngFor="let medico of medicos" [value]="medico.id_profesional">
                          {{medico.nombre_completo}}
                        </option>
                      </select>
                    </div>
                    <div class="col-md-3">
                      <label class="form-label">Desde:</label>
                      <input type="date" class="form-control campo" [(ngModel)]="filtroFechaInicio">
                    </div>
                    <div class="col-md-3">
                      <label class="form-label">Hasta:</label>
                      <input type="date" class="form-control campo" [(ngModel)]="filtroFechaFin">
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                      <button class="btn btn-primary w-100" (click)="buscarAgendas()">
                        <i class="fas fa-search"></i> Buscar
                      </button>
                    </div>
                  </div>

                  <div *ngIf="agendas.length === 0 && !cargandoAgendas" class="text-center text-muted py-4">
                    No se encontraron agendas
                  </div>

                  <div *ngIf="cargandoAgendas" class="text-center py-4">
                    <i class="fas fa-spinner fa-spin"></i> Cargando agendas...
                  </div>

                  <div class="row">
                    <div *ngFor="let agenda of agendas" class="col-md-6 mb-3">
                      <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                          <div>
                            <strong>{{agenda.nombre_medico}}</strong><br>
                            <small>{{agenda.fecha | date:'dd/MM/yyyy'}}</small>
                          </div>
                          <span class="badge" [class.bg-success]="agenda.activa" 
                                [class.bg-secondary]="!agenda.activa">
                            {{agenda.activa ? 'ACTIVA' : 'INACTIVA'}}
                          </span>
                        </div>
                        <div class="card-body">
                          <div class="mb-2">
                            <i class="fas fa-clock"></i> {{agenda.hora_inicio}} - {{agenda.hora_fin}}
                          </div>
                          <div class="mb-2">
                            <i class="fas fa-calendar-check"></i> Citas de {{agenda.duracion_cita}} min
                          </div>
                          <div *ngIf="agenda.observaciones" class="mb-2">
                            <i class="fas fa-comment"></i> {{agenda.observaciones}}
                          </div>
                          <div class="small">
                            <div *ngFor="let bloque of agenda.bloques" 
                                 class="d-flex justify-content-between border-bottom py-1">
                              <span>{{bloque.inicio}} - {{bloque.fin}}</span>
                              <span class="badge" [class.bg-success]="bloque.disponible" 
                                    [class.bg-warning]="!bloque.disponible">
                                {{bloque.disponible ? 'Libre' : 'Ocupado'}}
                              </span>
                            </div>
                          </div>
                          <div class="mt-3">
                            <button class="btn btn-danger btn-sm" (click)="abrirModalEliminarAgenda(agenda.id_agenda, agenda.fecha, agenda.profesional?.nombre_completo)">
                              <i class="fas fa-trash"></i> Eliminar
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="tab-pane fade" id="especialidades" role="tabpanel">
                  <div class="row">
                    <div class="col-md-6">
                      <h5>Asignar Especialidad</h5>
                      <form (ngSubmit)="asignarEspecialidad()" #espForm="ngForm">
                        <div class="mb-3">
                          <label class="form-label">Médico:</label>
                          <select class="form-select campo" [(ngModel)]="asignacionEsp.id_profesional" 
                                  name="profesional" required>
                            <option value="">Seleccione un médico</option>
                            <option *ngFor="let medico of medicos" [value]="medico.id_profesional">
                              {{medico.nombre_completo}}
                            </option>
                          </select>
                        </div>
                        <div class="mb-3">
                          <label class="form-label">Especialidad:</label>
                          <select class="form-select campo" [(ngModel)]="asignacionEsp.id_especialidad" 
                                  name="especialidad" required>
                            <option value="">Seleccione una especialidad</option>
                            <option *ngFor="let esp of especialidades" [value]="esp.id_especialidad">
                              {{esp.nombre}}
                            </option>
                          </select>
                        </div>
                        <div class="mb-3 form-check">
                          <input type="checkbox" class="form-check-input" 
                                 [(ngModel)]="asignacionEsp.es_principal" name="principal">
                          <label class="form-check-label">
                            Especialidad principal
                          </label>
                        </div>
                        <button type="submit" class="btn btn-success" [disabled]="!espForm.valid">
                          <i class="fas fa-plus"></i> Asignar Especialidad
                        </button>
                      </form>
                    </div>
                    
                    <div class="col-md-6">
                      <h5>Especialidades por Médico</h5>
                      <div *ngFor="let medico of medicos" class="mb-3">
                        <div class="card">
                          <div class="card-header">
                            <strong>{{medico.nombre_completo}}</strong>
                          </div>
                          <div class="card-body">
                            <div *ngIf="medico.especialidades.length === 0" class="text-muted">
                              Sin especialidades asignadas
                            </div>
                            <div *ngFor="let esp of medico.especialidades" 
                                 class="d-flex justify-content-between align-items-center mb-1">
                              <span>
                                {{esp.nombre}}
                                <span class="badge bg-primary ms-1" *ngIf="esp.es_principal">Principal</span>
                              </span>
                              <button class="btn btn-danger btn-sm" 
                                      (click)="abrirModalEliminarEspecialidad(medico.id_profesional, esp.id_especialidad, medico.nombre_completo, esp.nombre)">
                                <i class="fas fa-times"></i>
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>

      <div *ngIf="mensaje" class="toast-container position-fixed bottom-0 end-0 p-3">
        <div class="toast show" [class.bg-success]="tipoMensaje === 'success'" 
             [class.bg-danger]="tipoMensaje === 'error'">
          <div class="toast-body text-white">
            {{mensaje}}
          </div>
        </div>
      </div>

      <!-- Modal Eliminar Especialidad -->
      <div class="modal fade" [class.show]="mostrarModalEliminarEspecialidad" 
           [style.display]="mostrarModalEliminarEspecialidad ? 'block' : 'none'" 
           tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header bg-danger text-white">
              <h5 class="modal-title">
                <i class="fas fa-exclamation-triangle me-2"></i>Confirmar Eliminación
              </h5>
              <button type="button" class="btn-close btn-close-white" (click)="cerrarModalEliminarEspecialidad()"></button>
            </div>
            <div class="modal-body">
              <div class="text-center mb-3">
                <i class="fas fa-trash-alt text-danger" style="font-size: 3rem;"></i>
              </div>
              <p class="text-center mb-3">
                ¿Está seguro de quitar la especialidad <strong>{{especialidadAEliminar?.nombreEspecialidad}}</strong> 
                del médico <strong>{{especialidadAEliminar?.nombreMedico}}</strong>?
              </p>
              <div class="alert alert-warning">
                <i class="fas fa-info-circle me-2"></i>
                Esta acción no se puede deshacer.
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" (click)="cerrarModalEliminarEspecialidad()">
                <i class="fas fa-times me-2"></i>Cancelar
              </button>
              <button type="button" class="btn btn-danger" (click)="confirmarEliminarEspecialidad()">
                <i class="fas fa-trash me-2"></i>Eliminar Especialidad
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-backdrop fade" [class.show]="mostrarModalEliminarEspecialidad" 
           [style.display]="mostrarModalEliminarEspecialidad ? 'block' : 'none'"
           (click)="cerrarModalEliminarEspecialidad()"></div>

      <!-- Modal Eliminar Agenda -->
      <div class="modal fade" [class.show]="mostrarModalEliminarAgenda" 
           [style.display]="mostrarModalEliminarAgenda ? 'block' : 'none'" 
           tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header bg-danger text-white">
              <h5 class="modal-title">
                <i class="fas fa-exclamation-triangle me-2"></i>Confirmar Eliminación
              </h5>
              <button type="button" class="btn-close btn-close-white" (click)="cerrarModalEliminarAgenda()"></button>
            </div>
            <div class="modal-body">
              <div class="text-center mb-3">
                <i class="fas fa-calendar-times text-danger" style="font-size: 3rem;"></i>
              </div>
              <p class="text-center mb-3">
                ¿Está seguro de eliminar esta agenda?
              </p>
              <div *ngIf="agendaAEliminar?.fecha || agendaAEliminar?.medico" class="card mb-3">
                <div class="card-body">
                  <p class="mb-1" *ngIf="agendaAEliminar?.medico">
                    <i class="fas fa-user-md me-2"></i><strong>Médico:</strong> {{agendaAEliminar?.medico}}
                  </p>
                  <p class="mb-0" *ngIf="agendaAEliminar?.fecha">
                    <i class="fas fa-calendar me-2"></i><strong>Fecha:</strong> {{agendaAEliminar?.fecha}}
                  </p>
                </div>
              </div>
              <div class="alert alert-warning">
                <i class="fas fa-info-circle me-2"></i>
                Se eliminarán todos los bloques de horario asociados. Esta acción no se puede deshacer.
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" (click)="cerrarModalEliminarAgenda()">
                <i class="fas fa-times me-2"></i>Cancelar
              </button>
              <button type="button" class="btn btn-danger" (click)="confirmarEliminarAgenda()">
                <i class="fas fa-trash me-2"></i>Eliminar Agenda
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-backdrop fade" [class.show]="mostrarModalEliminarAgenda" 
           [style.display]="mostrarModalEliminarAgenda ? 'block' : 'none'"
           (click)="cerrarModalEliminarAgenda()"></div>
    </div>
  `,
  styleUrls: ['./gestion-horarios.css']
})
export class GestionHorariosComponent implements OnInit {
  medicos: MedicoResponse[] = [];
  especialidades: Especialidad[] = [];
  agendas: any[] = [];

  nuevaAgenda: AgendaDiariaRequest = {
    id_profesional: 0,
    fecha: '',
    hora_inicio: '',
    hora_fin: '',
    duracion_cita: 30,
    observaciones: '',
    bloques: []
  };

  asignacionEsp = {
    id_profesional: 0,
    id_especialidad: 0,
    es_principal: false
  };

  filtroMedico = '';
  filtroFechaInicio = '';
  filtroFechaFin = '';

  fechaMinima = '';
  mensaje = '';
  tipoMensaje: 'success' | 'error' = 'success';
  cargando = false;
  cargandoAgendas = false;

  mostrarModalEliminarEspecialidad = false;
  mostrarModalEliminarAgenda = false;
  especialidadAEliminar: { idProfesional: number; idEspecialidad: number; nombreMedico?: string; nombreEspecialidad?: string } | null = null;
  agendaAEliminar: { idAgenda: number; fecha?: string; medico?: string } | null = null;

  constructor(private http: HttpClient) {
    const today = new Date();
    this.fechaMinima = today.toISOString().split('T')[0];
  }

  ngOnInit() {
    window.scrollTo(0, 0);
    this.cargarMedicos();
    this.cargarEspecialidades();
  }

  private getHeaders() {
    const token = localStorage.getItem('token');
    return {
      headers: new HttpHeaders({
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      })
    };
  }

  async cargarMedicos() {
    try {
      const response = await this.http.get<MedicoResponse[]>('http://localhost:8000/horarios/medicos', this.getHeaders()).toPromise();
      this.medicos = response || [];
    } catch (error: any) {
      this.mostrarMensaje('Error al cargar médicos', 'error');
      console.error('Error:', error);
    }
  }

  async cargarEspecialidades() {
    try {
      const response = await this.http.get<Especialidad[]>('http://localhost:8000/horarios/especialidades', this.getHeaders()).toPromise();
      this.especialidades = response || [];
    } catch (error: any) {
      this.mostrarMensaje('Error al cargar especialidades', 'error');
      console.error('Error:', error);
    }
  }

  agregarBloque() {
    if (!this.nuevaAgenda.bloques) {
      this.nuevaAgenda.bloques = [];
    }
    this.nuevaAgenda.bloques.push({ inicio: '', fin: '' });
  }

  eliminarBloque(index: number) {
    if (this.nuevaAgenda.bloques) {
      this.nuevaAgenda.bloques.splice(index, 1);
    }
  }

  generarBloquesAutomaticos() {
    if (!this.nuevaAgenda.hora_inicio || !this.nuevaAgenda.hora_fin || !this.nuevaAgenda.duracion_cita) {
      this.mostrarMensaje('Debe especificar horario de inicio, fin y duración de cita primero', 'error');
      return;
    }

    const bloques: BloqueHora[] = [];
    const inicio = new Date(`2000-01-01T${this.nuevaAgenda.hora_inicio}:00`);
    const fin = new Date(`2000-01-01T${this.nuevaAgenda.hora_fin}:00`);
    
    let actual = new Date(inicio);
    while (actual.getTime() + (this.nuevaAgenda.duracion_cita * 60000) <= fin.getTime()) {
      const siguiente = new Date(actual.getTime() + (this.nuevaAgenda.duracion_cita * 60000));
      
      bloques.push({
        inicio: actual.toTimeString().substring(0, 5), 
        fin: siguiente.toTimeString().substring(0, 5)
      });
      
      actual = siguiente;
    }

    this.nuevaAgenda.bloques = bloques;
    this.mostrarMensaje(`Se generaron ${bloques.length} bloques automáticamente`, 'success');
  }

  calcularBloquesAutomaticos(): number {
    if (!this.nuevaAgenda.hora_inicio || !this.nuevaAgenda.hora_fin || !this.nuevaAgenda.duracion_cita) {
      return 0;
    }

    const inicio = new Date(`2000-01-01T${this.nuevaAgenda.hora_inicio}:00`);
    const fin = new Date(`2000-01-01T${this.nuevaAgenda.hora_fin}:00`);
    

    const duracionMs = this.nuevaAgenda.duracion_cita * 60000; 
    const tiempoTotalMs = fin.getTime() - inicio.getTime();
    
    return Math.floor(tiempoTotalMs / duracionMs);
  }

  getMedicoNombre(id: number): string {
    const medico = this.medicos.find(m => m.id_profesional === id);
    return medico?.nombre_completo || '';
  }

  async crearAgenda() {
    
    if (!this.nuevaAgenda.id_profesional) {
      this.mostrarMensaje('[WARNING] Debe seleccionar un médico', 'error');
      return;
    }
    
    if (!this.nuevaAgenda.fecha) {
      this.mostrarMensaje('[WARNING] Debe seleccionar una fecha', 'error');
      return;
    }
    
    // Validar que la fecha no sea pasada
    const fechaSeleccionada = new Date(this.nuevaAgenda.fecha);
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    
    if (fechaSeleccionada < hoy) {
      this.mostrarMensaje('[ERROR] No se pueden crear agendas para fechas pasadas', 'error');
      return;
    }
    
    
    const seismeses = new Date();
    seismeses.setMonth(seismeses.getMonth() + 6);
    if (fechaSeleccionada > seismeses) {
      this.mostrarMensaje('[WARNING] No se pueden crear agendas con más de 6 meses de anticipación', 'error');
      return;
    }
    
    if (!this.nuevaAgenda.hora_inicio || !this.nuevaAgenda.hora_fin) {
      this.mostrarMensaje('[WARNING] Debe especificar hora de inicio y fin', 'error');
      return;
    }
    
    // Validar que hora fin sea mayor que hora inicio
    const horaInicio = new Date(`2000-01-01T${this.nuevaAgenda.hora_inicio}:00`);
    const horaFin = new Date(`2000-01-01T${this.nuevaAgenda.hora_fin}:00`);
    
    if (horaFin <= horaInicio) {
      this.mostrarMensaje('[ERROR] La hora de fin debe ser posterior a la hora de inicio', 'error');
      return;
    }
    
    
    const duracionMinutos = (horaFin.getTime() - horaInicio.getTime()) / 60000;
    if (duracionMinutos < 60) {
      this.mostrarMensaje('[WARNING] La jornada debe tener al menos 1 hora de duración', 'error');
      return;
    }
    
    if (duracionMinutos > 720) {
      this.mostrarMensaje('[WARNING] La jornada no puede exceder las 12 horas', 'error');
      return;
    }
    
    if (!this.nuevaAgenda.duracion_cita || this.nuevaAgenda.duracion_cita < 15) {
      this.mostrarMensaje('[WARNING] La duración de cita debe ser al menos 15 minutos', 'error');
      return;
    }
    
    if (this.nuevaAgenda.duracion_cita > 240) {
      this.mostrarMensaje('[WARNING] La duración de cita no puede exceder 4 horas', 'error');
      return;
    }
    
    this.cargando = true;
    try {
      const response = await this.http.post('http://localhost:8000/horarios/agenda', this.nuevaAgenda, this.getHeaders()).toPromise();
      this.mostrarMensaje('[SUCCESS] Agenda creada exitosamente', 'success');
      this.limpiarFormulario();
      this.buscarAgendas(); 
    } catch (error: any) {
      const mensaje = error.error?.detail || 'Error al crear la agenda';
      this.mostrarMensaje('[ERROR] ' + mensaje, 'error');
      console.error('Error:', error);
    } finally {
      this.cargando = false;
    }
  }

  async buscarAgendas() {
    this.cargandoAgendas = true;
    try {
      let url = 'http://localhost:8000/horarios/agendas';
      const params = [];
      

      if (this.filtroMedico && this.filtroMedico.trim() !== '') {
        params.push(`id_profesional=${this.filtroMedico}`);
      }
      
      if (this.filtroFechaInicio) params.push(`fecha_inicio=${this.filtroFechaInicio}`);
      if (this.filtroFechaFin) params.push(`fecha_fin=${this.filtroFechaFin}`);
      if (params.length > 0) url += '?' + params.join('&');

      const response = await this.http.get<any[]>(url, this.getHeaders()).toPromise();
      this.agendas = response || [];

    } catch (error: any) {
      this.mostrarMensaje('Error al cargar agendas', 'error');
      console.error('Error:', error);
    } finally {
      this.cargandoAgendas = false;
    }
  }

  abrirModalEliminarAgenda(idAgenda: number, fecha?: string, medico?: string) {
    this.agendaAEliminar = { idAgenda, fecha, medico };
    this.mostrarModalEliminarAgenda = true;
  }

  cerrarModalEliminarAgenda() {
    this.mostrarModalEliminarAgenda = false;
    this.agendaAEliminar = null;
  }

  async confirmarEliminarAgenda() {
    if (!this.agendaAEliminar) return;

    try {
      await this.http.delete(`http://localhost:8000/horarios/agenda/${this.agendaAEliminar.idAgenda}`, this.getHeaders()).toPromise();
      this.mostrarMensaje('Agenda eliminada exitosamente', 'success');
      this.buscarAgendas();
      this.cerrarModalEliminarAgenda();
    } catch (error: any) {
      const mensaje = error.error?.detail || 'Error al eliminar la agenda';
      this.mostrarMensaje(mensaje, 'error');
    }
  }

  async asignarEspecialidad() {
    try {
      await this.http.post('http://localhost:8000/horarios/asignar-especialidad', this.asignacionEsp, this.getHeaders()).toPromise();
      this.mostrarMensaje('Especialidad asignada exitosamente', 'success');
      this.asignacionEsp = { id_profesional: 0, id_especialidad: 0, es_principal: false };
      this.cargarMedicos(); 
    } catch (error: any) {
      const mensaje = error.error?.detail || 'Error al asignar especialidad';
      this.mostrarMensaje(mensaje, 'error');
    }
  }

  abrirModalEliminarEspecialidad(idProfesional: number, idEspecialidad: number, nombreMedico?: string, nombreEspecialidad?: string) {
    this.especialidadAEliminar = { idProfesional, idEspecialidad, nombreMedico, nombreEspecialidad };
    this.mostrarModalEliminarEspecialidad = true;
  }

  cerrarModalEliminarEspecialidad() {
    this.mostrarModalEliminarEspecialidad = false;
    this.especialidadAEliminar = null;
  }

  async confirmarEliminarEspecialidad() {
    if (!this.especialidadAEliminar) return;

    try {
      await this.http.delete(`http://localhost:8000/horarios/especialidad/${this.especialidadAEliminar.idProfesional}/${this.especialidadAEliminar.idEspecialidad}`, this.getHeaders()).toPromise();
      this.mostrarMensaje('Especialidad removida exitosamente', 'success');
      this.cargarMedicos();
      this.cerrarModalEliminarEspecialidad();
    } catch (error: any) {
      const mensaje = error.error?.detail || 'Error al remover especialidad';
      this.mostrarMensaje(mensaje, 'error');
    }
  }

  limpiarFormulario() {
    this.nuevaAgenda = {
      id_profesional: 0,
      fecha: '',
      hora_inicio: '',
      hora_fin: '',
      duracion_cita: 30,
      observaciones: '',
      bloques: []
    };
  }

  private mostrarMensaje(texto: string, tipo: 'success' | 'error') {
    this.mensaje = texto;
    this.tipoMensaje = tipo;
    setTimeout(() => {
      this.mensaje = '';
    }, 5000);
  }
}
