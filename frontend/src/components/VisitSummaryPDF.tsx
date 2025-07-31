import React from 'react';
import { Document, Page, Text, View, StyleSheet, Font } from '@react-pdf/renderer';

// Register fonts (you can add custom fonts if needed)
Font.register({
  family: 'Helvetica',
  fonts: [
    { src: 'https://fonts.gstatic.com/s/helveticaneue/v70/1Ptsg8zYS_SKggPNyC0IT4ttDfA.ttf', fontWeight: 'normal' },
    { src: 'https://fonts.gstatic.com/s/helveticaneue/v70/1Ptsg8zYS_SKggPNyC0IT4ttDfB.ttf', fontWeight: 'bold' },
  ]
});

// Create styles
const styles = StyleSheet.create({
  page: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    padding: 40,
    fontFamily: 'Helvetica',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 30,
    borderBottom: '2px solid #2563eb',
    paddingBottom: 20,
  },
  logo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  logoText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2563eb',
    marginLeft: 10,
  },
  logoSubtext: {
    fontSize: 14,
    color: '#2563eb',
    marginLeft: 10,
    marginTop: -5,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#374151',
    textAlign: 'right',
  },
  content: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 20,
  },
  card: {
    backgroundColor: '#f8fafc',
    borderRadius: 8,
    padding: 20,
    marginBottom: 20,
    border: '1px solid #e2e8f0',
    flex: 1,
    minWidth: '45%',
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
    borderBottom: '1px solid #e2e8f0',
    paddingBottom: 10,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#374151',
    marginLeft: 12,
  },
  cardContent: {
    fontSize: 12,
    color: '#4b5563',
    lineHeight: 1.4,
  },
  bulletPoint: {
    flexDirection: 'row',
    marginBottom: 10,
    alignItems: 'flex-start',
  },
  bullet: {
    fontSize: 14,
    color: '#10b981',
    marginRight: 12,
    marginTop: 0,
    width: 20,
    textAlign: 'center',
  },
  bulletText: {
    fontSize: 12,
    color: '#4b5563',
    flex: 1,
  },
  warningBullet: {
    fontSize: 14,
    color: '#f59e0b',
    marginRight: 12,
    marginTop: 0,
    width: 20,
    textAlign: 'center',
  },
  infoBullet: {
    fontSize: 14,
    color: '#3b82f6',
    marginRight: 12,
    marginTop: 0,
    width: 20,
    textAlign: 'center',
  },
  nextSteps: {
    marginTop: 30,
    borderTop: '2px solid #2563eb',
    paddingTop: 20,
  },
  nextStepsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 20,
    textAlign: 'center',
  },
  stepsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-start',
  },
  step: {
    alignItems: 'center',
    flex: 1,
    paddingHorizontal: 10,
  },
  stepIcon: {
    fontSize: 28,
    color: '#2563eb',
    marginBottom: 12,
  },
  stepTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#374151',
    textAlign: 'center',
    marginBottom: 5,
  },
  stepSubtitle: {
    fontSize: 10,
    color: '#6b7280',
    textAlign: 'center',
  },
  medicationItem: {
    marginBottom: 12,
    padding: 12,
    backgroundColor: '#ffffff',
    borderRadius: 6,
    border: '1px solid #e5e7eb',
  },
  medicationName: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 4,
  },
  medicationDetails: {
    fontSize: 11,
    color: '#6b7280',
  },
  taskItem: {
    marginBottom: 10,
    padding: 10,
    backgroundColor: '#ffffff',
    borderRadius: 6,
    border: '1px solid #e5e7eb',
  },
  taskDescription: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 4,
  },
  taskDetails: {
    fontSize: 10,
    color: '#6b7280',
  },
  priority: {
    fontSize: 10,
    color: '#dc2626',
    fontWeight: 'bold',
  },
  mediumPriority: {
    fontSize: 10,
    color: '#f59e0b',
    fontWeight: 'bold',
  },
  lowPriority: {
    fontSize: 10,
    color: '#10b981',
    fontWeight: 'bold',
  },
  emptyState: {
    fontSize: 11,
    color: '#9ca3af',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  sectionIcon: {
    fontSize: 18,
    color: '#2563eb',
    marginRight: 8,
    width: 24,
    textAlign: 'center',
  },
});

interface VisitSummaryPDFProps {
  extraction: {
    follow_up_tasks: Array<{
      description: string;
      priority: string;
      due_date?: string;
      assigned_to?: string;
    }>;
    medication_instructions: Array<{
      medication_name: string;
      dosage: string;
      frequency: string;
      duration?: string;
      special_instructions?: string;
    }>;
    client_reminders: Array<{
      description: string;
      reminder_type: string;
      priority?: string;
      due_date?: string;
    }>;
    clinician_todos: Array<{
      description: string;
      task_type: string;
      priority?: string;
      due_date?: string;
    }>;
    custom_extractions?: Record<string, {
      extracted_data: string;
      confidence: string;
      reasoning?: string;
    }>;
  };
  patientName?: string;
  clinicName?: string;
  visitDate?: string;
}

const getPriorityText = (priority: string) => {
  switch (priority?.toLowerCase()) {
    case 'high': return '🔴 High';
    case 'medium': return '🟡 Medium';
    case 'low': return '🟢 Low';
    default: return '🟡 Medium';
  }
};

const VisitSummaryPDF: React.FC<VisitSummaryPDFProps> = ({ 
  extraction, 
  patientName = "Patient", 
  clinicName = "Animal Hospital",
  visitDate = new Date().toLocaleDateString()
}) => {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logo}>
            <Text style={styles.logoText}>🏥</Text>
            <View>
              <Text style={styles.logoText}>{clinicName}</Text>
              <Text style={styles.logoSubtext}>Medical Center</Text>
            </View>
          </View>
          <Text style={styles.title}>{patientName}&apos;s Visit Summary</Text>
        </View>

        {/* Main Content */}
        <View style={styles.content}>
                     {/* Summary of Findings */}
           <View style={styles.card}>
             <View style={styles.cardHeader}>
               <Text style={styles.sectionIcon}>🔍</Text>
               <Text style={styles.cardTitle}>Summary of Findings</Text>
             </View>
            <View style={styles.cardContent}>
                             {extraction.follow_up_tasks.length > 0 ? (
                 extraction.follow_up_tasks.slice(0, 3).map((task, index) => (
                   <View key={index} style={styles.bulletPoint}>
                     <Text style={styles.bullet}>▶</Text>
                     <Text style={styles.bulletText}>{task.description}</Text>
                   </View>
                 ))
               ) : (
                 <Text style={styles.emptyState}>No specific findings documented</Text>
               )}
            </View>
          </View>

                     {/* Patient Condition */}
           <View style={styles.card}>
             <View style={styles.cardHeader}>
               <Text style={styles.sectionIcon}>📋</Text>
               <Text style={styles.cardTitle}>Patient Assessment</Text>
             </View>
            <View style={styles.cardContent}>
              <Text>
                Patient presents with symptoms requiring medical attention. 
                {extraction.medication_instructions.length > 0 && ` ${extraction.medication_instructions.length} medication(s) prescribed.`}
                {extraction.follow_up_tasks.length > 0 && ` ${extraction.follow_up_tasks.length} follow-up task(s) identified.`}
                {' '}Overall condition requires monitoring and follow-up care.
              </Text>
            </View>
          </View>

                     {/* Home Care Instructions */}
           <View style={styles.card}>
             <View style={styles.cardHeader}>
               <Text style={styles.sectionIcon}>🏠</Text>
               <Text style={styles.cardTitle}>Home Care Instructions</Text>
             </View>
            <View style={styles.cardContent}>
              {extraction.client_reminders.length > 0 ? (
                extraction.client_reminders.map((reminder, index) => (
                  <View key={index} style={styles.bulletPoint}>
                    <Text style={styles.bullet}>✓</Text>
                    <Text style={styles.bulletText}>{reminder.description}</Text>
                  </View>
                ))
              ) : (
                <>
                  <View style={styles.bulletPoint}>
                    <Text style={styles.bullet}>✓</Text>
                    <Text style={styles.bulletText}>Monitor patient for any changes in condition</Text>
                  </View>
                  <View style={styles.bulletPoint}>
                    <Text style={styles.warningBullet}>⚠</Text>
                    <Text style={styles.bulletText}>Contact clinic if symptoms worsen</Text>
                  </View>
                  <View style={styles.bulletPoint}>
                    <Text style={styles.infoBullet}>ℹ</Text>
                    <Text style={styles.bulletText}>Follow medication schedule as prescribed</Text>
                  </View>
                </>
              )}
            </View>
          </View>

                     {/* Medications */}
           <View style={styles.card}>
             <View style={styles.cardHeader}>
               <Text style={styles.sectionIcon}>💊</Text>
               <Text style={styles.cardTitle}>Medications</Text>
             </View>
            <View style={styles.cardContent}>
              {extraction.medication_instructions.length > 0 ? (
                extraction.medication_instructions.map((med, index) => (
                  <View key={index} style={styles.medicationItem}>
                    <Text style={styles.medicationName}>{med.medication_name}</Text>
                    <Text style={styles.medicationDetails}>
                      {med.dosage} - {med.frequency}
                      {med.duration && ` • Duration: ${med.duration}`}
                    </Text>
                    {med.special_instructions && (
                      <Text style={styles.medicationDetails}>
                        Note: {med.special_instructions}
                      </Text>
                    )}
                  </View>
                ))
              ) : (
                <Text style={styles.emptyState}>No medications prescribed at this time</Text>
              )}
            </View>
          </View>
        </View>

        {/* What Happens Next */}
        <View style={styles.nextSteps}>
          <Text style={styles.nextStepsTitle}>📅 What Happens Next</Text>
                     <View style={styles.stepsContainer}>
             <View style={styles.step}>
               <Text style={styles.stepIcon}>🔍</Text>
               <Text style={styles.stepTitle}>Initial Assessment</Text>
               <Text style={styles.stepSubtitle}>Today</Text>
             </View>
             <View style={styles.step}>
               <Text style={styles.stepIcon}>📋</Text>
               <Text style={styles.stepTitle}>Follow-up Care</Text>
               <Text style={styles.stepSubtitle}>As scheduled</Text>
             </View>
             <View style={styles.step}>
               <Text style={styles.stepIcon}>📊</Text>
               <Text style={styles.stepTitle}>Recovery Monitoring</Text>
               <Text style={styles.stepSubtitle}>Ongoing</Text>
             </View>
           </View>
        </View>

                 {/* Additional Details */}
         {extraction.clinician_todos.length > 0 && (
           <View style={styles.card}>
             <View style={styles.cardHeader}>
               <Text style={styles.sectionIcon}>👨‍⚕️</Text>
               <Text style={styles.cardTitle}>Clinician Tasks</Text>
             </View>
            <View style={styles.cardContent}>
              {extraction.clinician_todos.map((todo, index) => (
                <View key={index} style={styles.taskItem}>
                  <Text style={styles.taskDescription}>{todo.description}</Text>
                  <Text style={styles.taskDetails}>
                    Type: {todo.task_type} • {getPriorityText(todo.priority ?? 'medium')}
                    {todo.due_date && ` • Due: ${todo.due_date}`}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Footer */}
        <View style={{ marginTop: 30, borderTop: '1px solid #e5e7eb', paddingTop: 20 }}>
          <Text style={{ fontSize: 10, color: '#6b7280', textAlign: 'center' }}>
            Generated on {visitDate} • {clinicName}
          </Text>
        </View>
      </Page>
    </Document>
  );
};

export default VisitSummaryPDF; 