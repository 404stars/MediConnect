import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { Navbar } from '../shared/navbar/navbar';
import { PacientesService, CitaPaciente, MotivoCancelacion, ReprogramarCitaRequest } from '../services/pacientes.service';
import { AuthService } from '../services/auth.service';

interface BloqueDisponible {
  id_bloque: number;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  especialidad: any;
  profesional: any;
  disponible?: boolean;
}

@Component({
  selector: 'app-mis-horas',
  templateUrl: './mis-horas.html',
  styleUrls: ['./mis-horas.css'],
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, Navbar]
})
export class MisHoras implements OnInit {
  citas: CitaPaciente[] = [];
  citasFiltradas: CitaPaciente[] = [];
  motivosCancelacion: MotivoCancelacion[] = [];
  isLoading: boolean = false;
  message: string = '';
  filtroEstado: string = '';
  
  showCancelModal: boolean = false;
  citaACancelar: CitaPaciente | null = null;
  motivoCancelacion: number = 1;
  observacionesCancelacion: string = '';

  showReprogramarModal: boolean = false;
  bloquesDisponibles: BloqueDisponible[] = [];
  bloqueSeleccionado: BloqueDisponible | null = null;
  isReprogramando: boolean = false;
  fechasDisponiblesReprogramar: string[] = [];
  fechaSeleccionadaReprogramar: string | null = null;
  bloquesFiltradosPorFechaReprogramar: BloqueDisponible[] = [];

  estados = [
    { valor: '', texto: 'Todas las citas' },
    { valor: 'AGENDADA', texto: 'Agendadas' },
    { valor: 'CONFIRMADA', texto: 'Confirmadas' },
    { valor: 'EN_ATENCION', texto: 'En Atención' },
    { valor: 'ATENDIDA', texto: 'Atendidas' },
    { valor: 'CANCELADA', texto: 'Canceladas' },
    { valor: 'NO_ASISTIO', texto: 'No Asistió' }
  ];

  constructor(
    private pacientesService: PacientesService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    window.scrollTo(0, 0);
    const activeRole = this.authService.getActiveRole();
    
    if (activeRole === 'Administrador' || activeRole === 'Recepcionista') {
      this.router.navigate(['/gestion-citas']);
      return;
    }
    
    if (activeRole === 'Médico') {
      this.router.navigate(['/agenda-medica']);
      return;
    }
    
    if (activeRole !== 'Paciente') {
      this.message = 'Esta sección está disponible solo para pacientes. Selecciona el rol de Paciente para continuar.';
      return;
    }
    
    this.cargarMotivos();
    this.cargarCitas();
  }

  cargarCitas() {
    this.isLoading = true;
    
    this.pacientesService.getMisCitas().subscribe({
      next: (citas) => {
        this.citas = citas;
        this.aplicarFiltro();
        this.isLoading = false;
      },
      error: (error) => {
        
        if (error.status === 401) {
          this.message = 'Sesión expirada. Por favor inicie sesión nuevamente.';
        } else if (error.status === 403) {
          this.message = 'No tiene permisos para ver las citas.';
        } else if (error.status === 0) {
          this.message = 'Error de conexión. Verifique que el servidor esté funcionando.';
        } else {
          this.message = `Error al cargar las citas (${error.status}): ${error.error?.detail || error.message}`;
        }
        
        this.isLoading = false;
      }
    });
  }

  cargarMotivos() {
    this.pacientesService.getMotivosCancelacion().subscribe({
      next: (motivos) => {
        this.motivosCancelacion = motivos;
        if (motivos.length > 0) {
          this.motivoCancelacion = motivos[0].id_motivo;
        }
      },
      error: (error) => {
      }
    });
  }

  aplicarFiltro() {
    if (this.filtroEstado === '') {
      this.citasFiltradas = this.citas;
    } else {
      this.citasFiltradas = this.citas.filter(cita => cita.estado === this.filtroEstado);
    }
  }

  onFiltroChange() {
    this.aplicarFiltro();
  }

  puedeSerCancelada(cita: CitaPaciente): boolean {
    if (!['AGENDADA', 'CONFIRMADA'].includes(cita.estado)) {
      return false;
    }
    
    const fechaHoraCita = new Date(`${cita.fecha}T${cita.hora_inicio}`);
    const ahora = new Date();
    
    return fechaHoraCita.getTime() > ahora.getTime();
  }

  puedeSerReprogramada(cita: CitaPaciente): boolean {
    return this.puedeSerCancelada(cita);
  }

  abrirModalCancelar(cita: CitaPaciente) {
    this.citaACancelar = cita;
    this.showCancelModal = true;
    this.observacionesCancelacion = '';
  }

  cerrarModalCancelar() {
    this.showCancelModal = false;
    this.citaACancelar = null;
    this.observacionesCancelacion = '';
  }

  confirmarCancelacion() {
    if (!this.citaACancelar) return;

    this.isLoading = true;
    this.pacientesService.cancelarCita(this.citaACancelar.id_cita, {
      id_motivo_cancelacion: this.motivoCancelacion,
      observaciones: this.observacionesCancelacion || undefined
    }).subscribe({
      next: () => {
        this.message = 'Cita cancelada exitosamente. Se ha enviado un correo de confirmación a su email.';
        this.cerrarModalCancelar();
        this.cargarCitas();
        this.isLoading = false;
      },
      error: (error) => {
        this.message = error.error?.detail || 'Error al cancelar la cita';
        this.isLoading = false;
      }
    });
  }

  abrirModalReprogramar(cita: CitaPaciente) {
    this.citaACancelar = cita;
    this.showReprogramarModal = true;
    this.bloqueSeleccionado = null;
    this.isReprogramando = false;
    this.observacionesCancelacion = '';
    this.fechaSeleccionadaReprogramar = null;
    this.bloquesFiltradosPorFechaReprogramar = [];

    this.pacientesService
      .getBloquesDisponibles({
        id_profesional: undefined,
        id_especialidad: undefined
      })
      .subscribe({
        next: (bloques: BloqueDisponible[]) => {
          const hoy = new Date();
          this.bloquesDisponibles = bloques.filter(b => {
            const especialidadNombre = typeof b.especialidad === 'string' 
              ? b.especialidad 
              : b.especialidad?.nombre || '';
            return new Date(b.fecha) > hoy && especialidadNombre === cita.especialidad;
          });
          
          this.fechasDisponiblesReprogramar = [...new Set(this.bloquesDisponibles.map(b => b.fecha))];
        },
        error: () => {
          this.bloquesDisponibles = [];
          this.fechasDisponiblesReprogramar = [];
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
    this.citaACancelar = null;
    this.bloqueSeleccionado = null;
    this.isReprogramando = false;
    this.observacionesCancelacion = '';
    this.fechaSeleccionadaReprogramar = null;
    this.bloquesFiltradosPorFechaReprogramar = [];
  }

  confirmarReprogramacion() {
    if (!this.citaACancelar || !this.bloqueSeleccionado) return;
    this.isReprogramando = true;

    this.pacientesService
      .reprogramarCita(this.citaACancelar.id_cita, {
        id_nuevo_bloque: this.bloqueSeleccionado.id_bloque,
        id_motivo_cancelacion: 1,
        observaciones: this.observacionesCancelacion || undefined
      })
      .subscribe({
        next: () => {
          this.message = 'Cita reprogramada exitosamente';
          this.cerrarModalReprogramar();
          this.cargarCitas();
          this.isReprogramando = false;
        },
        error: (error) => {
          this.message = error.error?.detail || 'Error al reprogramar la cita';
          this.isReprogramando = false;
        }
      });
  }

  getEstadoTexto(estado: string): string {
    const estadoObj = this.estados.find(e => e.valor === estado);
    return estadoObj ? estadoObj.texto : estado;
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
}
