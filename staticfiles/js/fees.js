
//⭐⭐⭐⭐⭐ ============Class-wise fee configuration & calculator

const classFeeMap = {
  'Class 6': { admission: 1500, tuition: 800, exam: 300, bus: 600, hostel: 2000, marksheet: 100 },
  'Class 7': { admission: 1600, tuition: 900, exam: 300, bus: 600, hostel: 2200, marksheet: 100 },
  'Class 8': { admission: 1700, tuition: 1000, exam: 400, bus: 700, hostel: 2400, marksheet: 100 },
  'Class 9': { admission: 2000, tuition: 1200, exam: 500, bus: 800, hostel: 2600, marksheet: 100 },
  'Class 10': { admission: 2200, tuition: 1300, exam: 600, bus: 900, hostel: 2800, marksheet: 100 }
};

function formatBDT(n){ return '৳ ' + (n||0).toLocaleString('en-BD'); }

function computeFee(cls, opts){
  const base = classFeeMap[cls] || {admission:0,tuition:0,exam:0,bus:0,hostel:0,marksheet:0};
  let total = base.admission + base.tuition + base.exam;
  if(opts.bus) total += base.bus;
  if(opts.hostel) total += base.hostel;
  if(opts.marksheet) total += base.marksheet; // Exact Marksheet choice
  return { ...base, total };
}

function updateFeePanel(){
  const cls = document.getElementById('admissionClass').value;
  const bus = document.getElementById('optBus').checked;
  const hostel = document.getElementById('optHostel').checked;
  const marksheet = document.getElementById('optExactMarksheet').checked;
  const fee = computeFee(cls,{bus,hostel,marksheet});
  for(const k of ['admission','tuition','exam','bus','hostel','marksheet','total']){
    const el=document.querySelector('[data-fee-'+k+']');
    if(el) el.textContent = formatBDT(fee[k]);
  }
}
document.addEventListener('change', (e)=>{
  if(['admissionClass','optBus','optHostel','optExactMarksheet'].includes(e.target.id)){
    updateFeePanel();
  }
});
document.addEventListener('DOMContentLoaded', updateFeePanel);

// Image preview helper
function previewPhoto(input, imgSelector='#photoPreview'){
  const file = input.files && input.files[0];
  const img = document.querySelector(imgSelector);
  if(file && img){
    img.src = URL.createObjectURL(file);
  }
}

// ⭐ End Class wise fee section===================================================


// ⭐⭐⭐⭐⭐=========================================STUDENT ID SECTION
 
function fillID(){
  idName.textContent = fName.value||'Student Name';
  idRoll.textContent = fRoll.value||'—';
  idClass.textContent = fClass.value||'—';
  idAddr.textContent = fAddr.value||'—';
  idUID.textContent = uid('STU');
  if(fPhoto.value) idPhoto.src = fPhoto.value;
}

// ⭐ End Student ID Section =====================================


//⭐⭐⭐⭐⭐ ==================attendance_staff JavaScript


const demoStudents = Array.from({length: 30}, (_,i)=>({name:'Student '+(i+1), roll: i+1})); 

function loadStudents(){
  const tbody = document.querySelector('#attTable tbody');
  tbody.innerHTML = '';
  demoStudents.forEach((s,idx)=>{
    const tr=document.createElement('tr');
    tr.innerHTML = `<td>${idx+1}</td><td>${s.name}</td><td>${s.roll}</td>
      <td><input type="checkbox" class="form-check-input present-toggle"></td>`;
    tbody.appendChild(tr);
  });
  document.getElementById('totalCount').textContent = demoStudents.length;
  updatePresentCount();
  tbody.addEventListener('change', updatePresentCount, {once:false});
}

function updatePresentCount(){
  const count = document.querySelectorAll('.present-toggle:checked').length;
  document.getElementById('presentCount').textContent = count;
}

function saveAttendance(){
  const rows=[...document.querySelectorAll('#attTable tbody tr')].map((tr,i)=>{
    return {
      name: tr.children[1].innerText,
      roll: tr.children[2].innerText,
      present: tr.querySelector('input').checked
    }
  });
  console.log('Saving (stub):', rows);
  alert('Saved locally (stub). Replace with API later.');
}

// ⭐ End Staff Attendance =====================================


// ⭐⭐⭐⭐⭐=================================Start Exam routine section

let exams=[
  {date:'2025-08-20', time:'10:00-12:00', cls:'Class 8', subject:'Math', room:'201'},
  {date:'2025-08-21', time:'10:00-12:00', cls:'Class 8', subject:'Science', room:'201'}
];
function render(){
  const q=(document.getElementById('examFilter').value||'').toLowerCase();
  const tbody=document.querySelector('#routineTable tbody');
  const data=exams.filter(x=>JSON.stringify(x).toLowerCase().includes(q));
  tbody.innerHTML = data.map((x,i)=>`<tr>
    <td>${i+1}</td><td>${x.date}</td><td>${x.time}</td><td>${x.cls}</td><td>${x.subject}</td><td>${x.room}</td>
    <td><button class='btn btn-sm btn-outline-danger' onclick='delExam(${i})'>Delete</button></td>
  </tr>`).join('');
}
function addExam(){
  exams.push({date:eDate.value, time:eTime.value, cls:eClass.value, subject:eSubject.value, room:eRoom.value});
  render();
}
function delExam(i){ exams.splice(i,1); render(); }
document.addEventListener('input', e=>{ if(e.target.id==='examFilter') render(); });
document.addEventListener('DOMContentLoaded', render);

// ⭐ End =====================================================================


// ⭐⭐⭐⭐⭐================ Start  hostel rooms

let rooms=[
  {no:'A-101', cap:4, occ:2}, {no:'A-102', cap:4, occ:4}, {no:'B-201', cap:3, occ:1},
  {no:'B-202', cap:3, occ:2}, {no:'C-301', cap:2, occ:0}
];
function renderRooms(){
  const grid=document.getElementById('roomGrid');
  grid.innerHTML = rooms.map(r=>`<div class="card-soft">
    <div class="d-flex justify-content-between"><strong>Room ${r.no}</strong><span>${r.occ}/${r.cap}</span></div>
    <div class="progress mt-2"><div class="progress-bar" style="width:${(r.occ/r.cap)*100}%"></div></div>
    <div class="small mt-1">${r.cap-r.occ>0?'<span class="text-success">Vacancy</span>':'<span class="text-danger">Full</span>'}</div>
  </div>`).join('');
  const sel=document.getElementById('hsRoom');
  sel.innerHTML = rooms.filter(r=>r.occ<r.cap).map(r=>`<option>${r.no}</option>`).join('');
}
function applyHostel(){
  const room=rooms.find(r=>r.no===document.getElementById('hsRoom').value);
  if(room && room.occ<room.cap){ room.occ++; renderRooms(); alert('Applied (stub). Hostel fee will be added in fee module.'); }
}
document.addEventListener('DOMContentLoaded', renderRooms);

//⭐ End  Library =======================================================



//⭐⭐⭐⭐⭐================ Start Library
let books=[
  {title:'Intro to Physics', author:'A. Rahman', isbn:'978-0001', copies:5},
  {title:'English Grammar', author:'S. Akter', isbn:'978-0002', copies:2}
];
function render(){
  const q=(libSearch.value||'').toLowerCase();
  const tbody=document.querySelector('#libTable tbody');
  const data=books.filter(x=>JSON.stringify(x).toLowerCase().includes(q));
  tbody.innerHTML = data.map((x,i)=>`<tr>
    <td>${i+1}</td><td>${x.title}</td><td>${x.author}</td><td>${x.isbn}</td><td>${x.copies}</td>
    <td>${x.copies>0?'<span class="badge bg-success">Available</span>':'<span class="badge bg-secondary">Out</span>'}</td>
    <td>
      <button class='btn btn-sm btn-outline-primary' onclick='issue(${i})'>Issue</button>
      <button class='btn btn-sm btn-outline-success' onclick='ret(${i})'>Return</button>
      <button class='btn btn-sm btn-outline-danger' onclick='delBook(${i})'>Delete</button>
    </td>
  </tr>`).join('');
}
function addBook(){ books.push({title:bTitle.value,author:bAuthor.value,isbn:bISBN.value,copies:Number(bCopies.value||1)}); render(); }
function delBook(i){ books.splice(i,1); render(); }
function issue(i){ if(books[i].copies>0){ books[i].copies--; render(); } else alert('No copies'); }
function ret(i){ books[i].copies++; render(); }
document.addEventListener('input', e=>{ if(e.target.id==='libSearch') render(); });
document.addEventListener('DOMContentLoaded', render);

//⭐ End  Library =======================================================


// ============================ Start Marks Entry ============================


function rowHTML(i,s){
  return `<tr>
    <td>${i+1}</td>
    <td>${s.name}</td>
    <td>${s.roll}</td>
    <td><input class="form-control form-control-sm score" type="number" min="0" max="100" value="0"></td>
    <td><input class="form-control form-control-sm score" type="number" min="0" max="100" value="0"></td>
    <td><input class="form-control form-control-sm score" type="number" min="0" max="100" value="0"></td>
    <td><input class="form-control form-control-sm score" type="number" min="0" max="100" value="0"></td>
    <td class="gpa">0.00</td>
  </tr>`;
}

function computeGPA(scores){
  let total = scores.reduce((sum,obj)=> sum + obj.score, 0);
  let avg = total / scores.length;
  return (avg/20).toFixed(2); // GPA scale: 100 → 5.00
}

function loadMarks(){
  const tbody=document.querySelector('#marksTable tbody');
  tbody.innerHTML = demoStudents.map((s,i)=>rowHTML(i,s)).join('');
  tbody.addEventListener('input', (e)=>{
    if(e.target.classList.contains('score')){
      const tr=e.target.closest('tr');
      const scores=[...tr.querySelectorAll('.score')].map(inp=>({score: Number(inp.value||0), weight:1}));
      tr.querySelector('.gpa').innerText = computeGPA(scores);
    }
  });
}

function saveMarks(){
  const rows=[...document.querySelectorAll('#marksTable tbody tr')].map(tr=>{
    const tds=[...tr.children];
    const scores=[...tr.querySelectorAll('.score')].map(inp=>Number(inp.value||0));
    return { 
      name: tds[1].innerText, 
      roll: tds[2].innerText, 
      subjects: {Bangla:scores[0], English:scores[1], Math:scores[2], Science:scores[3]}, 
      gpa: tr.querySelector('.gpa').innerText 
    };
  });
  console.log('Saving (stub):', rows);
  alert('Marks saved locally (stub). Replace with API later.');
}

// ============================ End Marks Entry ============================