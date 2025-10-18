import { Component, OnInit } from '@angular/core';
import { Navbar } from '../shared/navbar/navbar';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { AuthService } from '../services/auth.service';

interface BloqueDisponible {
  id_bloque: number;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  especialidad: string;
  profesional: string;
}

interface MotivoCancelacion {
  id_motivo: number;
  descripcion: string;
}

@Component({
  selector: 'app-agenda-medica',
  imports: [Navbar, FormsModule, CommonModule],
  templateUrl: './agenda-medica.html',
  styleUrl: './agenda-medica.css'
})
export class AgendaMedica implements OnInit {
  private apiUrl = 'http://127.0.0.1:8000';
  
  fechaSeleccionada: string = '';
  citas: any[] = [];
  todasLasCitas: any[] = [];
  motivosCancelacion: MotivoCancelacion[] = [];
  bloquesDisponibles: BloqueDisponible[] = [];
  mostrarCanceladas: boolean = false;
  
  showCancelModal: boolean = false;
  showReprogramarModal: boolean = false;
  citaSeleccionada: any = null;
  
  motivoCancelacion: number = 1;
  observacionesCancelacion: string = '';
  bloqueSeleccionado: BloqueDisponible | null = null;
  
  isLoading: boolean = false;
  isReprogramando: boolean = false;
  
  fechasDisponiblesReprogramar: string[] = [];
  fechaSeleccionadaReprogramar: string | null = null;
  bloquesFiltradosPorFechaReprogramar: BloqueDisponible[] = [];
  
  message: string = '';
  
  userInfo: any = null;

  constructor(private http: HttpClient, private authService: AuthService) {}

  ngOnInit(): void {
    window.scrollTo(0, 0);
    this.authService.getUserAdditionalInfo().subscribe({
      next: (info) => {
        this.userInfo = info;
        this.authService.saveAdditionalInfo(info);
        this.cargarTodasCitas();
      },
      error: (error) => {
        console.error('Error al cargar información adicional:', error);
        this.cargarTodasCitas();
      }
    });
    this.cargarMotivos();
  }

  cargarTodasCitas() {
    this.isLoading = true;
    
    const activeRole = this.authService.getActiveRole();
    let url = `${this.apiUrl}/pacientes/admin/todas-las-citas?skip=0&limit=100&active_role=${activeRole}`;
    
    // El backend filtra por profesional_id si el rol activo es "Médico"
    console.log('Cargando citas con rol activo:', activeRole);
    
    this.http.get<any[]>(url)
      .subscribe({
        next: (data) => {
          this.todasLasCitas = data;
          this.aplicarFiltro();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error cargando citas:', error);
          this.message = '[ERROR] Error al cargar las citas';
          this.isLoading = false;
        }
      });
  }

  aplicarFiltro() {
    if (this.mostrarCanceladas) {
      this.citas = [...this.todasLasCitas];
    } else {
      this.citas = this.todasLasCitas.filter(cita => cita.estado !== 'CANCELADA');
    }
  }

  onMostrarCanceladasChange() {
    this.aplicarFiltro();
  }

  cargarMotivos() {
    this.http.get<MotivoCancelacion[]>(`${this.apiUrl}/pacientes/motivos-cancelacion`)
      .subscribe({
        next: (motivos) => {
          this.motivosCancelacion = motivos;
          if (motivos.length > 0) {
            this.motivoCancelacion = motivos[0].id_motivo;
          }
        },
        error: (error) => {
          console.error('Error cargando motivos:', error);
        }
      });
  }

  abrirModalCancelar(cita: any) {
    if (!cita || !this.puedeCancelar(cita)) {
      this.message = '[WARNING] Esta cita no puede ser cancelada';
      setTimeout(() => this.message = '', 3000);
      return;
    }
    
    this.citaSeleccionada = cita;
    this.showCancelModal = true;
    this.observacionesCancelacion = '';
  }

  cerrarModalCancelar() {
    this.showCancelModal = false;
    this.citaSeleccionada = null;
    this.observacionesCancelacion = '';
  }

  confirmarCancelacion() {
    if (!this.citaSeleccionada) {
      this.message = '[WARNING] No hay cita seleccionada';
      setTimeout(() => this.message = '', 3000);
      return;
    }

    if (!this.motivoCancelacion) {
      this.message = '[WARNING] Debe seleccionar un motivo de cancelación';
      setTimeout(() => this.message = '', 3000);
      return;
    }

    this.isLoading = true;
    const body = {
      id_motivo_cancelacion: this.motivoCancelacion,
      observaciones: this.observacionesCancelacion || 'Cancelada por administrador'
    };

    this.http.post(`${this.apiUrl}/pacientes/admin/cancelar-cita/${this.citaSeleccionada.id_cita}`, body)
      .subscribe({
        next: () => {
          this.message = '[SUCCESS] Cita cancelada exitosamente. Se ha enviado notificación al paciente.';
          this.cerrarModalCancelar();
          this.cargarTodasCitas();
          this.isLoading = false;
          setTimeout(() => this.message = '', 5000);
        },
        error: (error) => {
          this.message = '[ERROR] Error al cancelar: ' + (error.error?.detail || 'Error desconocido');
          this.isLoading = false;
          setTimeout(() => this.message = '', 5000);
        }
      });
  }

  abrirModalReprogramar(cita: any) {
    if (!cita || !this.puedeReprogramar(cita)) {
      this.message = 'Esta cita no puede ser reprogramada';
      setTimeout(() => this.message = '', 3000);
      return;
    }
    
    this.citaSeleccionada = cita;
    this.showReprogramarModal = true;
    this.bloqueSeleccionado = null;
    this.observacionesCancelacion = '';
    this.fechaSeleccionadaReprogramar = null;
    this.bloquesFiltradosPorFechaReprogramar = [];
    
    this.http.get<BloqueDisponible[]>(`${this.apiUrl}/pacientes/bloques-disponibles`)
      .subscribe({
        next: (bloques) => {
          const hoy = new Date();
          hoy.setHours(0, 0, 0, 0);
          
          const especialidadCita = cita.profesional?.especialidad?.nombre || '';
          
          this.bloquesDisponibles = bloques.filter(b => {
            const [year, month, day] = b.fecha.split('-').map(Number);
            const fechaBloque = new Date(year, month - 1, day);
            fechaBloque.setHours(0, 0, 0, 0);
            
            const especialidadNombre = typeof b.especialidad === 'string' 
              ? b.especialidad 
              : (b.especialidad as any)?.nombre || '';
            
            return fechaBloque > hoy && especialidadNombre === especialidadCita;
          });
          
          this.fechasDisponiblesReprogramar = [...new Set(this.bloquesDisponibles.map(b => b.fecha))];
          
          if (this.bloquesDisponibles.length === 0) {
            this.message = 'No hay bloques disponibles para reprogramar';
          }
        },
        error: (error) => {
          console.error('Error cargando bloques:', error);
          this.bloquesDisponibles = [];
          this.fechasDisponiblesReprogramar = [];
          this.message = 'Error al cargar bloques disponibles';
          setTimeout(() => this.message = '', 3000);
        }
      });
  }

  seleccionarFechaReprogramar(fecha: string) {
    this.fechaSeleccionadaReprogramar = fecha;
    this.bloqueSeleccionado = null;
    this.bloquesFiltradosPorFechaReprogramar = this.bloquesDisponibles.filter(b => b.fecha === fecha);
  }

  formatearFechaCalendario(fecha: string): string {
    const [year, month, day] = fecha.split('-');
    const fechaObj = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    const dias = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    return `${dias[fechaObj.getDay()]} ${day} ${meses[fechaObj.getMonth()]}`;
  }

  cerrarModalReprogramar() {
    this.showReprogramarModal = false;
    this.citaSeleccionada = null;
    this.bloqueSeleccionado = null;
    this.observacionesCancelacion = '';
    this.fechaSeleccionadaReprogramar = null;
    this.bloquesFiltradosPorFechaReprogramar = [];
  }

  confirmarReprogramacion() {
    if (!this.citaSeleccionada) {
      this.message = '[WARNING] No hay cita seleccionada';
      setTimeout(() => this.message = '', 3000);
      return;
    }

    if (!this.bloqueSeleccionado) {
      this.message = '[WARNING] Debe seleccionar un nuevo horario';
      setTimeout(() => this.message = '', 3000);
      return;
    }

    this.isReprogramando = true;
    const body = {
      id_nuevo_bloque: this.bloqueSeleccionado.id_bloque,
      id_motivo_cancelacion: 1,
      observaciones: this.observacionesCancelacion || 'Reprogramada por administrador'
    };

    this.http.post(`${this.apiUrl}/pacientes/admin/reprogramar-cita/${this.citaSeleccionada.id_cita}`, body)
      .subscribe({
        next: () => {
          this.message = '[SUCCESS] Cita reprogramada exitosamente. Se ha enviado notificación al paciente.';
          this.cerrarModalReprogramar();
          this.cargarTodasCitas();
          this.isReprogramando = false;
          setTimeout(() => this.message = '', 5000);
        },
        error: (error) => {
          this.message = '[ERROR] Error al reprogramar: ' + (error.error?.detail || 'Error desconocido');
          this.isReprogramando = false;
          setTimeout(() => this.message = '', 5000);
        }
      });
  }

  showAtendidaModal: boolean = false;
  showNoAsistioModal: boolean = false;
  citaParaMarcar: any = null;

  abrirModalAtendida(cita: any) {
    if (!cita || !this.puedemarcarAtendida(cita)) {
      this.message = '[WARNING] Esta cita no puede ser marcada como atendida';
      setTimeout(() => this.message = '', 3000);
      return;
    }
    
    this.citaParaMarcar = cita;
    this.showAtendidaModal = true;
  }

  cerrarModalAtendida() {
    this.showAtendidaModal = false;
    this.citaParaMarcar = null;
  }

  confirmarAtendida() {
    if (!this.citaParaMarcar) {
      this.message = '[WARNING] No hay cita seleccionada';
      setTimeout(() => this.message = '', 3000);
      return;
    }

    this.isLoading = true;
    this.http.put(`${this.apiUrl}/pacientes/admin/marcar-atendida/${this.citaParaMarcar.id_cita}`, {})
      .subscribe({
        next: () => {
          this.message = '[SUCCESS] Cita marcada como atendida exitosamente';
          this.cerrarModalAtendida();
          this.cargarTodasCitas();
          this.isLoading = false;
          setTimeout(() => this.message = '', 5000);
        },
        error: (error) => {
          this.message = '[ERROR] Error al marcar como atendida: ' + (error.error?.detail || 'Error desconocido');
          this.isLoading = false;
          setTimeout(() => this.message = '', 5000);
        }
      });
  }

  abrirModalNoAsistio(cita: any) {
    if (!cita || !this.puedeMarcarNoAsistio(cita)) {
      this.message = '[WARNING] Esta cita no puede ser marcada como no asistida';
      setTimeout(() => this.message = '', 3000);
      return;
    }
    
    this.citaParaMarcar = cita;
    this.showNoAsistioModal = true;
  }

  cerrarModalNoAsistio() {
    this.showNoAsistioModal = false;
    this.citaParaMarcar = null;
  }

  confirmarNoAsistio() {
    if (!this.citaParaMarcar) {
      this.message = '[WARNING] No hay cita seleccionada';
      setTimeout(() => this.message = '', 3000);
      return;
    }

    this.isLoading = true;
    this.http.put(`${this.apiUrl}/pacientes/admin/marcar-no-asistio/${this.citaParaMarcar.id_cita}`, {})
      .subscribe({
        next: () => {
          this.message = '[SUCCESS] Cita marcada como no asistió exitosamente';
          this.cerrarModalNoAsistio();
          this.cargarTodasCitas();
          this.isLoading = false;
          setTimeout(() => this.message = '', 5000);
        },
        error: (error) => {
          this.message = '[ERROR] Error al marcar como no asistió: ' + (error.error?.detail || 'Error desconocido');
          this.isLoading = false;
          setTimeout(() => this.message = '', 5000);
        }
      });
  }

  formatearFecha(fecha: string): string {
    const [year, month, day] = fecha.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.toLocaleDateString('es-ES', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  formatearHora(hora: string): string {
    return new Date(`2000-01-01T${hora}`).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  getEstadoClase(estado: string): string {
    switch (estado) {
      case 'AGENDADA':
        return 'badge bg-primary';
      case 'CONFIRMADA':
        return 'badge bg-success';
      case 'EN_ATENCION':
        return 'badge bg-warning text-dark';
      case 'ATENDIDA':
        return 'badge bg-info';
      case 'CANCELADA':
        return 'badge bg-danger';
      case 'NO_ASISTIO':
        return 'badge bg-secondary';
      default:
        return 'badge bg-light text-dark';
    }
  }

  getEstadoTexto(estado: string): string {
    const estados: { [key: string]: string } = {
      'AGENDADA': 'Agendada',
      'CONFIRMADA': 'Confirmada',
      'EN_ATENCION': 'En Atención',
      'ATENDIDA': 'Atendida',
      'CANCELADA': 'Cancelada',
      'NO_ASISTIO': 'No Asistió'
    };
    return estados[estado] || estado;
  }

  puedeModificarCita(cita: any): boolean {
    return cita && (cita.estado === 'AGENDADA' || cita.estado === 'CONFIRMADA');
  }

  puedeCancelar(cita: any): boolean {
    return this.puedeModificarCita(cita);
  }

  puedeReprogramar(cita: any): boolean {
    return this.puedeModificarCita(cita);
  }

  puedemarcarAtendida(cita: any): boolean {
    return this.puedeModificarCita(cita);
  }

  puedeMarcarNoAsistio(cita: any): boolean {
    return this.puedeModificarCita(cita);
  }

}

