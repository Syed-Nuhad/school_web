
// Common helpers: CSV/PDF export, GPA calc, ID generator
function exportTableToCSV(tableSelector, filename='export.csv'){
  const rows=[...document.querySelectorAll(tableSelector+' tr')];
  const csv=rows.map(tr=>[...tr.children].map(td=>JSON.stringify(td.innerText)).join(',')).join('\n');
  const blob=new Blob([csv],{type:'text/csv'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=filename;a.click();
}

async function exportElementToPDF(elSelector, filename='document.pdf'){
  // simple print-to-pdf fallback
  window.print();
  // For real usage, plug jsPDF + html2canvas here later
}

function computeGPA(marks){
  // marks: array of {score, weight} where weight defaults 1
  // simple 5-point scale example
  const gradePoint = (m)=> m>=80?5: m>=70?4: m>=60?3.5: m>=50?3: m>=40?2:0;
  const total=marks.reduce((acc,m)=>acc+(m.weight||1),0)||1;
  const sum=marks.reduce((acc,m)=>acc+gradePoint(m.score)*(m.weight||1),0);
  return (sum/total).toFixed(2);
}

function uid(prefix='ID'){
  return prefix+'-'+Math.random().toString(36).slice(2,8).toUpperCase();
}
