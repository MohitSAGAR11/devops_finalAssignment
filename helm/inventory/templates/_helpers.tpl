{{/* Base name for every resource: "<release>" if it already contains the chart name, else "<release>-inventory". */}}
{{- define "inventory.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "inventory.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/* Selector labels for one component; usage: include "inventory.selectorLabels" (list . "backend") */}}
{{- define "inventory.selectorLabels" -}}
{{- $root := index . 0 -}}
app.kubernetes.io/name: {{ $root.Chart.Name }}
app.kubernetes.io/instance: {{ $root.Release.Name }}
app.kubernetes.io/component: {{ index . 1 }}
{{- end -}}

{{- define "inventory.postgresHost" -}}
{{ include "inventory.fullname" . }}-postgres
{{- end -}}
