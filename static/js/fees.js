/* =========================
   FEE PANEL (safe on any page)
   ========================= */
(function FeePanel() {
  const clsEl      = document.getElementById('admissionClass');
  const busEl      = document.getElementById('optBus');
  const hostelEl   = document.getElementById('optHostel');
  const marksheetEl= document.getElementById('optExactMarksheet');

  if (!clsEl || !busEl || !hostelEl || !marksheetEl) return; // not on this page

  const classFeeMap = {
    'Class 6':  { admission:1500, tuition:800,  exam:300, bus:600, hostel:2000, marksheet:100 },
    'Class 7':  { admission:1600, tuition:900,  exam:300, bus:600, hostel:2200, marksheet:100 },
    'Class 8':  { admission:1700, tuition:1000, exam:400, bus:700, hostel:2400, marksheet:100 },
    'Class 9':  { admission:2000, tuition:1200, exam:500, bus:800, hostel:2600, marksheet:100 },
    'Class 10': { admission:2200, tuition:1300, exam:600, bus:900, hostel:2800, marksheet:100 },
  };
  const fmt = n => '৳ ' + (n || 0).toLocaleString('en-BD');

  function computeFee(cls, opts) {
    const base = classFeeMap[cls] || {admission:0,tuition:0,exam:0,bus:0,hostel:0,marksheet:0};
    let total = base.admission + base.tuition + base.exam;
    if (opts.bus)       total += base.bus;
    if (opts.hostel)    total += base.hostel;
    if (opts.marksheet) total += base.marksheet;
    return { ...base, total };
  }

  function updateFeePanel() {
    const fee = computeFee(clsEl.value, {
      bus:       !!busEl.checked,
      hostel:    !!hostelEl.checked,
      marksheet: !!marksheetEl.checked
    });
    ['admission','tuition','exam','bus','hostel','marksheet','total'].forEach(k => {
      const el = document.querySelector(`[data-fee-${k}]`);
      if (el) el.textContent = fmt(fee[k]);
    });
  }

  document.addEventListener('change', (e) => {
    if (e.target === clsEl || e.target === busEl || e.target === hostelEl || e.target === marksheetEl) {
      updateFeePanel();
    }
  });
  updateFeePanel();
})();

/* =========================
   STUDENT ID helpers (guarded)
   ========================= */
(function StudentID() {
  // only wire if the form exists
  const fName  = document.getElementById('fName');
  const fRoll  = document.getElementById('fRoll');
  const fClass = document.getElementById('fClass');
  const fAddr  = document.getElementById('fAddr');
  const fPhoto = document.getElementById('fPhotoFile');
  const card   = document.getElementById('idCard');
  if (!card) return;

  const idName = document.getElementById('idName');
  const idRoll = document.getElementById('idRoll');
  const idClass= document.getElementById('idClass');
  const idAddr = document.getElementById('idAddr');
  const idUID  = document.getElementById('idUID');
  const idPhoto= document.getElementById('idPhoto');

  function uid(prefix='STU') {
    return `${prefix}-${Math.floor(Math.random()*9000+1000)}`;
  }

  window.fillID = function fillID() {
    idName.textContent  = fName?.value  || '—';
    idRoll.textContent  = fRoll?.value  || '—';
    idClass.textContent = fClass?.value || '—';
    idAddr.textContent  = fAddr?.value  || '—';
    idUID.textContent   = uid('STU');

    if (fPhoto?.files && fPhoto.files[0]) {
      const reader = new FileReader();
      reader.onload = e => { idPhoto.src = e.target.result; };
      reader.readAsDataURL(fPhoto.files[0]);
    }
  };
})();

/* =========================
   STAFF ATTENDANCE (guarded)
   ========================= */
(function StaffAttendance() {
  const table = document.getElementById('attTable');
  const total = document.getElementById('totalCount');
  const pres  = document.getElementById('presentCount');
  if (!table || !total || !pres) return;

  const demoStudents = Array.from({length:30}, (_,i)=>({name:`Student ${i+1}`, roll:i+1}));

  function updatePresentCount(){
    pres.textContent = table.querySelectorAll('.present-toggle:checked').length;
  }

  function loadStudents(){
    const tbody = table.querySelector('tbody');
    tbody.innerHTML = '';
    demoStudents.forEach((s,idx)=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${idx+1}</td><td>${s.name}</td><td>${s.roll}</td>
        <td><input type="checkbox" class="form-check-input present-toggle"></td>`;
      tbody.appendChild(tr);
    });
    total.textContent = demoStudents.length;
    updatePresentCount();
    tbody.addEventListener('change', updatePresentCount);
  }

  window.saveAttendance = function saveAttendance(){
    const rows=[...table.querySelectorAll('tbody tr')].map(tr=>({
      name: tr.children[1].innerText,
      roll: tr.children[2].innerText,
      present: tr.querySelector('input').checked
    }));
    console.log('Saving (stub):', rows);
    alert('Saved locally (stub). Replace with API later.');
  };

  loadStudents();
})();

/* =========================
   EXAM ROUTINE (guarded, no global name "render")
   ========================= */
(function ExamRoutine() {
  const filterEl = document.getElementById('examFilter');
  const table = document.getElementById('routineTable');
  if (!filterEl || !table) return;

  let exams = [
    {date:'2025-08-20', time:'10:00-12:00', cls:'Class 8', subject:'Math',    room:'201'},
    {date:'2025-08-21', time:'10:00-12:00', cls:'Class 8', subject:'Science', room:'201'}
  ];

  function renderExamTable(){
    const q = (filterEl.value || '').toLowerCase();
    const tbody = table.querySelector('tbody');
    const data = exams.filter(x => JSON.stringify(x).toLowerCase().includes(q));
    tbody.innerHTML = data.map((x,i)=>`
      <tr>
        <td>${i+1}</td><td>${x.date}</td><td>${x.time}</td>
        <td>${x.cls}</td><td>${x.subject}</td><td>${x.room}</td>
        <td><button class="btn btn-sm btn-outline-danger" data-del="${i}">Delete</button></td>
      </tr>`).join('');
  }

  window.addExam = function addExam(){
    const eDate = document.getElementById('eDate');
    const eTime = document.getElementById('eTime');
    const eClass= document.getElementById('eClass');
    const eSubject=document.getElementById('eSubject');
    const eRoom = document.getElementById('eRoom');
    if (!eDate || !eTime || !eClass || !eSubject || !eRoom) return;
    exams.push({date:eDate.value, time:eTime.value, cls:eClass.value, subject:eSubject.value, room:eRoom.value});
    renderExamTable();
  };

  table.addEventListener('click', (e)=>{
    const btn = e.target.closest('[data-del]');
    if (!btn) return;
    const idx = Number(btn.dataset.del);
    exams.splice(idx,1);
    renderExamTable();
  });

  filterEl.addEventListener('input', renderExamTable);
  renderExamTable();
})();

/* =========================
   HOSTEL ROOMS (guarded)
   ========================= */
(function Hostel() {
  const grid = document.getElementById('roomGrid');
  const sel  = document.getElementById('hsRoom');
  if (!grid || !sel) return;

  let rooms = [
    {no:'A-101', cap:4, occ:2}, {no:'A-102', cap:4, occ:4},
    {no:'B-201', cap:3, occ:1}, {no:'B-202', cap:3, occ:2},
    {no:'C-301', cap:2, occ:0}
  ];

  function renderRooms(){
    grid.innerHTML = rooms.map(r=>`
      <div class="card-soft">
        <div class="d-flex justify-content-between">
          <strong>Room ${r.no}</strong><span>${r.occ}/${r.cap}</span>
        </div>
        <div class="progress mt-2">
          <div class="progress-bar" style="width:${(r.occ/r.cap)*100}%"></div>
        </div>
        <div class="small mt-1">
          ${r.cap-r.occ>0 ? '<span class="text-success">Vacancy</span>' : '<span class="text-danger">Full</span>'}
        </div>
      </div>`).join('');
    sel.innerHTML = rooms.filter(r=>r.occ<r.cap).map(r=>`<option>${r.no}</option>`).join('');
  }

  window.applyHostel = function applyHostel(){
    const room = rooms.find(r=>r.no===sel.value);
    if (room && room.occ < room.cap) { room.occ++; renderRooms(); alert('Applied (stub).'); }
  };

  renderRooms();
})();

/* =========================
   LIBRARY (guarded, no global name "render")
   ========================= */
(function Library() {
  const searchEl = document.getElementById('libSearch');
  const table    = document.getElementById('libTable');
  if (!table || !searchEl) return;

  let books = [
    {title:'Intro to Physics', author:'A. Rahman', isbn:'978-0001', copies:5},
    {title:'English Grammar',  author:'S. Akter',  isbn:'978-0002', copies:2},
  ];

  function renderLibrary(){
    const q = (searchEl.value || '').toLowerCase();
    const tbody = table.querySelector('tbody');
    const data = books.filter(x => JSON.stringify(x).toLowerCase().includes(q));
    tbody.innerHTML = data.map((x,i)=>`
      <tr>
        <td>${i+1}</td><td>${x.title}</td><td>${x.author}</td>
        <td>${x.isbn}</td><td>${x.copies}</td>
        <td>${x.copies>0?'<span class="badge bg-success">Available</span>':'<span class="badge bg-secondary">Out</span>'}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" data-issue="${i}">Issue</button>
          <button class="btn btn-sm btn-outline-success" data-ret="${i}">Return</button>
          <button class="btn btn-sm btn-outline-danger" data-del="${i}">Delete</button>
        </td>
      </tr>`).join('');
  }

  // expose addBook if you call it from a form/button
  window.addBook = function addBook(){
    const bTitle = document.getElementById('bTitle');
    const bAuthor= document.getElementById('bAuthor');
    const bISBN  = document.getElementById('bISBN');
    const bCopies= document.getElementById('bCopies');
    if (!bTitle || !bAuthor || !bISBN || !bCopies) return;
    books.push({title:bTitle.value, author:bAuthor.value, isbn:bISBN.value, copies:Number(bCopies.value||1)});
    renderLibrary();
  };

  table.addEventListener('click', (e)=>{
    const iDel = e.target.closest('[data-del]');  if (iDel) { books.splice(+iDel.dataset.del,1); renderLibrary(); return; }
    const iIss = e.target.closest('[data-issue]');if (iIss) { const i=+iIss.dataset.issue; if (books[i].copies>0) { books[i].copies--; renderLibrary(); } return; }
    const iRet = e.target.closest('[data-ret]');  if (iRet) { books[+iRet.dataset.ret].copies++; renderLibrary(); return; }
  });

  searchEl.addEventListener('input', renderLibrary);
  renderLibrary();
})();