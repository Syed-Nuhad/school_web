const $ = (id) => document.getElementById(id);

// ⭐ END Initialize AOS ==============================================================================


// ⭐⭐⭐⭐⭐============================= START: Navigation Menu Script 

// ⭐ ======= START: Select Elements 

const mobileMenu = document.getElementById("mobile-menu");
const navLinks = document.querySelector(".nav-links");

// ⭐ END: Select Elements ==============================================================================






  // ⭐⭐⭐⭐⭐ =============================== START: Banner Slider Script 

// ⭐ ================== START: Select Elements 

const slides = document.querySelectorAll(".slide");
const prevBtn = document.querySelector(".prev");
const nextBtn = document.querySelector(".next");
const dotsContainer = document.querySelector(".dots");
// ===== END: Select Elements ===============================================================================

let currentIndex = 0;



// ⭐⭐⭐⭐⭐============================= START: Show Specific Slide 

function showSlide(index) {
  slides.forEach(slide => slide.classList.remove("active"));
  dots.forEach(dot => dot.classList.remove("active"));

  slides[index].classList.add("active");
  dots[index].classList.add("active");

  currentIndex = index;
}


// ⭐ END Show Specific Slide =============================================================================





// ⭐ END: Banner Slider Script =========================================================================



// ⭐⭐⭐⭐⭐=================================START MARKSHEET Download pdf

// (Keeping your old html2canvas attempt commented exactly as you had it)
//   document.getElementById("downloadPdf").addEventListener("click", function () {
//   const { jsPDF } = window.jspdf;
//   const marksheet = document.getElementById("marksheet");
//   html2canvas(marksheet, { scale: 2 }).then(canvas => {
//     const imgData = canvas.toDataURL("image/png");
//     const pdf = new jsPDF("p", "mm", "a4");
//     // Calculate width and height for A4
//     const pdfWidth = pdf.internal.pageSize.getWidth();
//     const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
//     pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
//     pdf.save("marksheet.pdf");
//   });
// });

// (Removed duplicate Student Data + Marksheet logic to avoid conflicts)
  
  
  // ⭐⭐⭐⭐⭐==============Start : Number Animation

document.addEventListener("DOMContentLoaded", () => {
  const progressCircles = document.querySelectorAll(".progress-circle");

  progressCircles.forEach(circle => {
    const span = circle.querySelector("span");
    if (!span) return;

    const currentValue = parseInt(span.textContent);
    if (isNaN(currentValue)) return;

    // Find the total value from sibling .total circle inside the same parent container

    let totalValue = null;
    const parentFlex = circle.closest(".d-flex");
    if (parentFlex) {
      const totalCircleSpan = parentFlex.querySelector(".progress-circle.total span");
      if (totalCircleSpan) {
        totalValue = parseInt(totalCircleSpan.textContent);
      }
    }

    if (totalValue && totalValue > 0) {
      // Calculate attendance percentage
      const percent = Math.round((currentValue / totalValue) * 100);

      // Choose color based on class type
      let color = "#007bff"; // default blue for total
      if (circle.classList.contains("present")) {
        if (circle.classList.contains("class1")) color = "#28a745"; // green
        else if (circle.classList.contains("class2")) color = "#ffc107"; // yellow
        else if (circle.classList.contains("class3")) color = "#dc3545"; // red
        else color = "#28a745"; // fallback green
      }

      // Update background conic-gradient with dynamic percentage
      circle.style.background = `conic-gradient(${color} 0% ${percent}%, #e0e0e0 ${percent}% 100%)`;

      // Animate number from 0 to currentValue
      animateNumber(span, currentValue, 1000);
    }
  });
});


//

// ⭐⭐⭐⭐⭐=============Start Number animation function

function animateNumber(element, end, duration) {
  let start = 0;
  let range = end - start;
  let increment = end > start ? 1 : -1;
  let stepTime = range === 0 ? duration : Math.abs(Math.floor(duration / range));
  let current = start;

  let timer = setInterval(() => {
    current += increment;
    element.textContent = current;
    if (current === end) {
      clearInterval(timer);
    }
  }, stepTime);
}

  // ⭐End : Number Animation  ==================================================================



    // ⭐⭐⭐⭐⭐===================Start : Circle Progress


document.addEventListener("DOMContentLoaded", function () {
  const circles = document.querySelectorAll(".circle-progress");

  circles.forEach(circle => {
    let value = parseFloat(circle.getAttribute("data-value"));
    
    // Convert actual value into percentage of circle circumference
    // Assuming "data-value" is already a percentage (0–100):
    let offset = 100 - value;
    circle.style.strokeDashoffset = offset;
  });
});

// ⭐ End : Circle Progress  =====================================================================================





// ⭐⭐⭐⭐⭐ Start Accademy section :Course filter (pure front-end)

  document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('#academics .filter-btn');
    const cards = document.querySelectorAll('#academics .course-card');

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        cards.forEach(card => {
          if (filter === 'all' || card.dataset.category === filter) {
            card.style.display = '';
          } else {
            card.style.display = 'none';
          }
        });
      });
    });
  });


// ---- Syllabus data (example, multi-page friendly) ----

// ⭐ End Accademy section :Course filter (pure front-end) ========================================================



// ⭐⭐⭐⭐⭐================ Start CONTACT SECTION STYLES



document.getElementById('contact-form').addEventListener('submit', function(e){
  e.preventDefault();
  alert("Thank you! Your message will be sent once backend is connected.");
});

// ⭐ End CONTACT SECTION STYLES ====================================================================================

  // ⭐⭐⭐⭐⭐===================== Start About Section Image Fade-in animation and cycling images  

  document.addEventListener("DOMContentLoaded", () => {
    // Fade-in for right text
    const fadeElems = document.querySelectorAll(".fade-in");
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("show");
        }
      });
    }, { threshold: 0.2 });
    fadeElems.forEach(el => observer.observe(el));

    // Image cycling
    const images = document.querySelectorAll(".image-fade-container img.fade-image");
    let current = 0;
    const total = images.length;
    const intervalTime = 4000; // 4 seconds per image

    function showNextImage() {
      images[current].classList.remove("active");
      current = (current + 1) % total;
      images[current].classList.add("active");
    }

    setInterval(showNextImage, intervalTime);
  });



  // ⭐ END End: About Section Image Fade-in animation =========================================


  // ⭐⭐⭐⭐⭐===================== Start Bootstrap Carousel Initialization

  document.addEventListener('DOMContentLoaded', () => {
    const aboutCarouselEl = document.querySelector('#aboutCarousel');
    if (aboutCarouselEl) {
      const aboutCarousel = new bootstrap.Carousel(aboutCarouselEl, {
        interval: 3500,
        ride: 'carousel',
        pause: false,
        wrap: true
      });
    }
  });

  // ⭐ END Bootstrap Carousel Initialization ===================================




// (Removed duplicate TOTAL SUMMARY SCRIPT block)  ================================================================ 

//

// ---------------------------------------------------------------
 //  Utilities: grading + image loading
//----------------------------------------------------------------
function gradeFromScore(obtained, full) {
  const pct = (obtained / full) * 100;
  if (pct >= 80) return "A+";
  if (pct >= 70) return "A";
  if (pct >= 60) return "A-";
  if (pct >= 50) return "B";
  if (pct >= 40) return "C";
  if (pct >= 33) return "D";
  return "F";
}

// Convert <img> or URL to dataURL (for jsPDF backgrounds/logos)
function loadImageAsDataURL(imgElOrUrl) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      try {
        const c = document.createElement("canvas");
        c.width = img.naturalWidth;
        c.height = img.naturalHeight;
        const ctx = c.getContext("2d");
        ctx.drawImage(img, 0, 0);
        resolve(c.toDataURL("image/png"));
      } catch (e) {
        resolve(null);
      }
    };
    img.onerror = () => resolve(null);
    img.src = typeof imgElOrUrl === "string" ? imgElOrUrl : imgElOrUrl.src;
  });
}

// ---------------------------------------------------------------
//   Demo student data (Class + Section so we can rank properly)
//   NOTE: You can replace this with your real data source.

const students = [
  {
    name: "John Doe", roll: "05", class: "10", section: "A",
    marks: [
      { subject: "Mathematics", obtained: 92, full: 100 },
      { subject: "English",     obtained: 85, full: 100 },
      { subject: "Science",     obtained: 88, full: 100 },
    ],
    attendance: { present: 180, absent: 5 }
  },
  {
    name: "Jane Smith", roll: "12", class: "10", section: "A",
    marks: [
      { subject: "Mathematics", obtained: 90, full: 100 },
      { subject: "English",     obtained: 89, full: 100 },
      { subject: "Science",     obtained: 86, full: 100 },
    ],
    attendance: { present: 181, absent: 4 }
  },
  {
    name: "Rahim Khan", roll: "07", class: "10", section: "A",
    marks: [
      { subject: "Mathematics", obtained: 90, full: 100 },
      { subject: "English",     obtained: 89, full: 100 },
      { subject: "Science",     obtained: 84, full: 100 },
    ],
    attendance: { present: 179, absent: 6 }
  },
  {
    name: "Sara Ali", roll: "02", class: "10", section: "B",
    marks: [
      { subject: "Mathematics", obtained: 95, full: 100 },
      { subject: "English",     obtained: 78, full: 100 },
      { subject: "Science",     obtained: 80, full: 100 },
    ],
    attendance: { present: 182, absent: 3 }
  },
  {
    name: "Anik Das", roll: "11", class: "1", section: "A",
    marks: [
      { subject: "Math",    obtained: 80, full: 100 },
      { subject: "Science", obtained: 75, full: 100 },
      { subject: "English", obtained: 85, full: 100 },
    ],
  },
];

//---------------------------------------------------------------
 //  DOM references
//----------------------------------------------------------------
const form = document.getElementById("searchForm");
const marksheet = document.getElementById("marksheet");
const msName = document.getElementById("msName");
const msRoll = document.getElementById("msRoll");
const msClass = document.getElementById("msClass");
const msSection = document.getElementById("msSection");
const marksBody = document.getElementById("marksBody");
const totalFullMarksEl = document.getElementById("totalFullMarks");
const totalMarksEl = document.getElementById("totalMarks");
const finalGradeEl = document.getElementById("finalGrade");
const finalPositionEl = document.getElementById("finalPosition");
const daysPresentEl = document.getElementById("daysPresent");
const daysAbsentEl = document.getElementById("daysAbsent");
const printBtn = document.getElementById("printBtn");
const downloadBtn = document.getElementById("downloadPdf");

let currentStudent = null;

//---------------------------------------------------------------
 //  Rank calculation within (class, section)
  // Returns an integer rank (1 = best)
//----------------------------------------------------------------
function totalOf(student) {
  return student.marks.reduce((s, m) => s + (Number(m.obtained) || 0), 0);
}

function rankInSection(target, all) {
  const peers = all
    .filter(s => s.class === target.class && s.section === target.section)
    .map(s => ({ name: s.name, roll: s.roll, total: totalOf(s) }))
    .sort((a, b) => b.total - a.total);

  // competition ranking (1,2,2,4)
  let rank = 0, prev = null, skipped = 0;
  for (let i = 0; i < peers.length; i++) {
    const cur = peers[i];
    if (prev === null || cur.total < prev) {
      rank = i + 1;
      // For dense ranking (1,2,2,3), use: rank = (prev===null ? 1 : rank+1);
    }
    prev = cur.total;
    if (cur.roll === target.roll && cur.name === target.name) return rank;
  }
  return peers.length; // fallback
}

// ---------------------------------------------------------------
 //  Render marksheet for a found student
//----------------------------------------------------------------
function showMarksheet(student) {
  // basic info
  msName.textContent = student.name;
  msRoll.textContent = student.roll;
  msClass.textContent = student.class; // keep just the number to match your original
  msSection.textContent = student.section;

  // totals + rows + position
  marksBody.innerHTML = "";
  let totalFull = 0, totalObt = 0;
  student.marks.forEach(m => {
    totalFull += Number(m.full) || 0;
    totalObt += Number(m.obtained) || 0;
  });

  const position = rankInSection(student, students);
  const finalGrade = gradeFromScore(totalObt, totalFull);

  // Build rows (repeat position in each row to satisfy “column shows position”)
  student.marks.forEach(m => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${m.subject}</td>
      <td>${m.full}</td>
      <td>${m.obtained}</td>
      <td>${gradeFromScore(m.obtained, m.full)}</td>
      <td>${position}</td>
    `;
    marksBody.appendChild(tr);
  });

  // Fill footer
  totalFullMarksEl.textContent = totalFull;
  totalMarksEl.textContent = totalObt;
  finalGradeEl.textContent = finalGrade;
  finalPositionEl.textContent = position;

  // Attendance (if provided in data)
  if (student.attendance) {
    daysPresentEl.textContent = student.attendance.present;
    daysAbsentEl.textContent = student.attendance.absent;
  }

  marksheet.style.display = "block";
}
// ----- Marksheet search (safe) -----
(() => {
  const form = document.getElementById('searchForm');
  if (!form) return;                 // no form on this page → do nothing

  const marksheet       = document.getElementById('marksheet');
  const msName          = document.getElementById('msName');
  const msRoll          = document.getElementById('msRoll');
  const msClass         = document.getElementById('msClass');
  const msSection       = document.getElementById('msSection');
  const marksBody       = document.getElementById('marksBody');
  const totalFullMarksEl= document.getElementById('totalFullMarks');
  const totalMarksEl    = document.getElementById('totalMarks');
  const finalGradeEl    = document.getElementById('finalGrade');
  const finalPositionEl = document.getElementById('finalPosition');
  const daysPresentEl   = document.getElementById('daysPresent');
  const daysAbsentEl    = document.getElementById('daysAbsent');
  const printBtn        = document.getElementById('printBtn');
  const downloadBtn     = document.getElementById('downloadPdf');

  // helper to read form inputs safely (including the field literally named "class")
  const get = name => form.elements[name]?.value ?? '';

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const name    = get('name').trim().toLowerCase();
    const roll    = get('roll').trim();
    const cls     = get('class').trim();     // <- read the input named "class"
    const section = get('section').trim();

    const found = students.find((s) =>
      (name === '' || s.name.toLowerCase().includes(name)) &&
      (roll === '' || s.roll === roll) &&
      (cls  === '' || s.class === cls) &&
      (section === '' || s.section === section)
    );

    if (!found) {
      alert('No student found with the given details.');
      if (marksheet) marksheet.style.display = 'none';
      return;
    }

    // your existing render function can be called here
    showMarksheet(found);
  });

  // bind print / pdf only if the buttons exist
  printBtn?.addEventListener('click', () => window.print());
  downloadBtn?.addEventListener('click', async () => {
    // ... your existing jsPDF code ...
  });
})();
// ---------------------------------------------------------------
//   Print + PDF (Letter size, with background + logo) — SAFE
// ---------------------------------------------------------------
(() => {
  const marksheet       = document.getElementById('marksheet');
  const printBtn        = document.getElementById('printBtn');
  const downloadBtn     = document.getElementById('downloadPdf');
  if (!marksheet || (!printBtn && !downloadBtn)) return; // this page has no marksheet

  const daysPresentEl   = document.getElementById('daysPresent');
  const daysAbsentEl    = document.getElementById('daysAbsent');

  // `currentStudent` is set by your search flow; if it isn't, we’ll guard below.

  printBtn?.addEventListener('click', () => window.print());

  downloadBtn?.addEventListener('click', async () => {
    if (!window.currentStudent) {
      alert('Please search for a student first.');
      return;
    }

    const { jsPDF } = window.jspdf || {};
    if (!jsPDF) return alert('jsPDF not loaded. Please include jsPDF and jspdf-autotable.');
    const doc = new jsPDF({ orientation: 'p', unit: 'mm', format: 'letter' });

    if (typeof doc.autoTable !== 'function') {
      return alert('jsPDF AutoTable plugin not loaded. Please include it after jsPDF.');
    }

    const pageWidth  = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();

    // Read template-supplied STATIC_URL to locate assets reliably (see #2 below)
    const STATIC = (window.STATIC_URL || '/static/').replace(/\/?$/, '/');

    const collegeName = (document.getElementById('collegeName')?.textContent || 'College Name').trim();
    const examName    = (document.getElementById('examName')?.textContent || 'Examination').trim();

    const logoImgEl   = marksheet.querySelector('img');
    const logoDataURL = logoImgEl ? await loadImageAsDataURL(logoImgEl) : null;

    // ✅ Use STATIC_URL so the path works no matter where this JS file lives
    const bgDataURL   = await loadImageAsDataURL(`${STATIC}img/background/marksheet-bg.png`);

    const drawFrameAndHeader = () => {
      if (bgDataURL) doc.addImage(bgDataURL, 'PNG', 0, 0, pageWidth, pageHeight, '', 'FAST');
      doc.setDrawColor(0,0,0); doc.setLineWidth(0.6);
      doc.rect(8, 8, pageWidth - 16, pageHeight - 16);
      if (logoDataURL) doc.addImage(logoDataURL, 'PNG', 12, 12, 20, 20);
      doc.setFont(undefined, 'bold'); doc.setFontSize(16);
      doc.text(collegeName, pageWidth/2, 18, { align: 'center' });
      doc.setFont(undefined, 'normal'); doc.setFontSize(12);
      doc.text(examName, pageWidth/2, 24, { align: 'center' });
      doc.setLineWidth(0.3);
      doc.line(10, 32, pageWidth - 10, 32);
    };

    drawFrameAndHeader();

    // Student info
    const s = window.currentStudent;
    doc.setFontSize(11);
    let y = 38;
    doc.text(`Name: ${s.name}`, 12, y);
    doc.text(`Roll No: ${s.roll}`, pageWidth / 2, y);
    y += 6;
    doc.text(`Class: ${s.class}`, 12, y);
    doc.text(`Section: ${s.section}`, pageWidth / 2, y);

    const totalFull = s.marks.reduce((sum, m) => sum + Number(m.full || 0), 0);
    const totalObt  = s.marks.reduce((sum, m) => sum + Number(m.obtained || 0), 0);
    const position  = rankInSection(s, window.students || []);
    const finalGrade= gradeFromScore(totalObt, totalFull);

    const tableBody = s.marks.map(m => [
      m.subject,
      String(m.full),
      String(m.obtained),
      gradeFromScore(m.obtained, m.full),
      String(position)
    ]);

    doc.autoTable({
      head: [['Subject','Full Marks','Marks Obtained','Grade Obtained','Position']],
      body: tableBody,
      foot: [['Total', String(totalFull), String(totalObt), String(finalGrade), String(position)]],
      startY: 50,
      theme: 'grid',
      headStyles: { fillColor: [13,110,253], textColor: 255 },
      footStyles: { fillColor: [220,220,220], textColor: 0, fontStyle: 'bold' },
      styles: { fontSize: 11, cellPadding: 2 },
      margin: { left: 12, right: 12 },
      didDrawPage: drawFrameAndHeader
    });

    // Attendance + signatures
    let afterTableY = doc.lastAutoTable.finalY + 8;
    const presentText = s.attendance?.present ?? (daysPresentEl?.textContent || '');
    const absentText  = s.attendance?.absent  ?? (daysAbsentEl?.textContent  || '');
    if (presentText || absentText) {
      doc.setFontSize(11);
      doc.text(`Days Present: ${presentText || '—'}   |   Days Absent: ${absentText || '—'}`, 12, afterTableY);
      afterTableY += 10;
    }
    const sigY = Math.min(afterTableY + 10, pageHeight - 30);
    const leftX = 20, rightX = pageWidth - 20;
    doc.line(leftX, sigY, leftX + 60, sigY);
    doc.line(rightX - 60, sigY, rightX, sigY);
    doc.setFontSize(10);
    doc.text("Parent's Signature", leftX, sigY + 6);
    doc.text("Class Teacher's Signature", rightX - 60, sigY + 6);

    doc.save(`Marksheet_${s.name.replace(/\s+/g,'_')}.pdf`);
  });
})();

// ⭐⭐⭐⭐⭐ Start: Academic Calendar Animations (Fade + Typing Dates)

document.addEventListener("DOMContentLoaded", () => {
  const fadeElems = document.querySelectorAll("[data-aos='fade-up']");
  const typingDates = document.querySelectorAll(".typing-date");

  // Fade animation observer
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("aos-animate");
      }
    });
  }, { threshold: 0.2 });

  fadeElems.forEach(el => observer.observe(el));

  // Typing animation for dates
  typingDates.forEach(dateElem => {
    const text = dateElem.getAttribute("data-text");
    let index = 0;

    const type = () => {
      if (index < text.length) {
        dateElem.textContent += text.charAt(index);
        index++;
        setTimeout(type, 50); // typing speed
      } else {
        dateElem.style.borderRight = "none"; // remove cursor after typing
      }
    };

    // Trigger typing when element enters viewport
    const typeObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          type();
          typeObserver.unobserve(dateElem);
        }
      });
    }, { threshold: 0.5 });

    typeObserver.observe(dateElem);
  });
});
// ⭐ End: Academic Calendar Animations ====================================================================


// ⭐⭐⭐⭐⭐ ====================== Start: Dashboard Section JS  

// Members data (local images)
const membersData = {
  hod: [
    { img: "./team_member_1.png", name: "Dr. Rahman", role: "Head of Department", post: "Professor", bio: "Oversees the academic department and coordinates curriculum." },
    { img: "./img/hod2.jpeg", name: "Dr. Ali", role: "Head of Department", post: "Senior Lecturer", bio: "Focuses on research and student mentorship." },
    { img: "./img/hod3.jpeg", name: "Prof. Anwar", role: "Head of Department", post: "Research Head", bio: "Manages department-wide research initiatives and conferences." }
  ],
  teachers: [
    { img: "./img/teacher1.jpeg", name: "Ms. Ayesha", role: "Teacher", post: "Science Faculty", bio: "Specialist in physics and chemistry education." },
    { img: "./img/teacher2.jpeg", name: "Mr. Hasan", role: "Teacher", post: "Mathematics Faculty", bio: "Expert in advanced mathematics and problem-solving." },
    { img: "./img/teacher3.jpeg", name: "Mrs. Khan", role: "Teacher", post: "Arts Faculty", bio: "Teaches fine arts and design thinking." }
  ],
  students: [
    { img: "./img/student1.jpeg", name: "Shakil Ahmed", role: "Student", post: "B.Sc. Physics", section: "A", bio: "Active in college sports and debate society." },
    { img: "./img/student2.jpeg", name: "Mariya Khan", role: "Student", post: "B.A. English", section: "B", bio: "Member of literary club and cultural activities." },
    { img: "./img/student3.jpeg", name: "Nabil", role: "Student", post: "B.Com", section: "C", bio: "Enjoys business strategy and campus volunteering." }
  ],
  staff: [
    { img: "./img/staff1.jpeg", name: "Mr. Karim", role: "Staff", post: "Lab Technician", bio: "Maintains lab equipment and assists in experiments." },
    { img: "./img/staff2.jpeg", name: "Mr. Rafiq", role: "Staff", post: "Office Admin", bio: "Handles administrative and clerical tasks." },
    { img: "./img/staff3.jpeg", name: "Ms. Fatima", role: "Staff", post: "Library Manager", bio: "Manages library resources and helps students find information." }
  ]
};

let currentCategory = '';
let currentPage = 1;
const perPage = 6;
let autoSlideInterval;

function loadMembers(category, page = 1) {
  const membersContainer = document.getElementById('membersContainer');
  membersContainer.innerHTML = '';
  currentCategory = category;
  currentPage = page;

  const members = membersData[category];
  const start = (page - 1) * perPage;
  const paginatedMembers = members.slice(start, start + perPage);

  paginatedMembers.forEach(member => {
    membersContainer.innerHTML += `
      <div class="col-md-6 mb-4">
        <div class="member-item ${member.role.toLowerCase()} ${member.role.toLowerCase() === 'student' ? 'student' : ''}">
          <img src="${member.img}" alt="${member.name}">
          <div style="flex:1">
            <h6 class="fw-bold mb-1">${member.name} <small class="text-muted">(${member.role})</small></h6>
            <p class="text-muted mb-2">Post: ${member.post}</p>
            <div class="member-bio">${member.bio}</div>
          </div>
        </div>
      </div>
    `;
  });

  // Pagination
  const totalPages = Math.ceil(members.length / perPage);
  const pagination = document.getElementById('membersPagination');
  pagination.innerHTML = '';
  for (let i = 1; i <= totalPages; i++) {
    pagination.innerHTML += `
      <li class="page-item ${i === page ? 'active' : ''}">
        <a class="page-link" href="#">${i}</a>
      </li>
    `;
  }

  document.querySelectorAll('#membersPagination .page-link').forEach((link, index) => {
    link.addEventListener('click', e => {
      e.preventDefault();
      clearInterval(autoSlideInterval);
      loadMembers(currentCategory, index + 1);
    });
  });

  clearInterval(autoSlideInterval);
  autoSlideInterval = setInterval(() => {
    let nextPage = currentPage + 1;
    if (nextPage > totalPages) nextPage = 1;
    loadMembers(currentCategory, nextPage);
  }, 4000);
}

// Show modal and load members
document.querySelectorAll('.view-all-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.preventDefault();
    loadMembers(btn.dataset.category);
    new bootstrap.Modal(document.getElementById('membersModal')).show();
  });
});
// ---- Dashboard "members" filters (defensive) ----
document.addEventListener('DOMContentLoaded', () => {
  const $ = (id) => document.getElementById(id);

  const fc  = $('filterClass');
  const fs  = $('filterSection');
  const vab = $('viewAllBtn');
  const box = $('membersContainer');

  // If the members UI isn't on this page, bail early
  if (!box || !fc || !fs || !vab) return;

  fc.addEventListener('change', applyFilters);
  fs.addEventListener('change', applyFilters);
  vab.addEventListener('click', (e) => {
    e.preventDefault();
    fc.value = '';
    fs.value = '';
    // Reload current list if helper is present
    if (typeof loadMembers === 'function') {
      const cat = window.currentCategory || Object.keys(window.membersData || {teachers:[]})[0] || 'teachers';
      loadMembers(cat, 1);
    } else {
      applyFilters();
    }
  });

  function applyFilters() {
    const classFilter   = fc.value;
    const sectionFilter = fs.value;

    const data = (window.membersData && window.currentCategory)
      ? (membersData[currentCategory] || [])
      : [];

    const filtered = data.filter(m => {
      const okClass   = classFilter   ? m.post === classFilter : true;
      const okSection = sectionFilter ? (m.section || '') === sectionFilter : true;
      return okClass && okSection;
    });

    box.innerHTML = filtered.map(member => `
      <div class="col-md-6 mb-4">
        <div class="member-item ${member.role.toLowerCase()} ${member.role.toLowerCase() === 'student' ? 'student' : ''}">
          <img src="${member.img}" alt="${member.name}">
          <div style="flex:1">
            <h6 class="fw-bold mb-1">${member.name}
              <small class="text-muted">(${member.role})</small>
            </h6>
            <p class="text-muted mb-2">Post: ${member.post}</p>
            <div class="member-bio">${member.bio}</div>
          </div>
        </div>
      </div>
    `).join('');
  }
});



//⭐⭐⭐⭐⭐ Start Collage Cultural Fest Section -->

  function openVideoModal(videoSrc) {
    const modalVideo = document.getElementById('modalVideo');
    modalVideo.src = videoSrc;
    const videoModal = new bootstrap.Modal(document.getElementById('videoModal'));
    videoModal.show();
    videoModal._element.addEventListener('hidden.bs.modal', () => {
      modalVideo.pause();
      modalVideo.src = '';
    });
  }


// ⭐ END Collage Cultural Fest Section

// Class wise result summary section


// counter for student info

// ⭐⭐⭐⭐⭐ Number Counter Animation for Summary + Circles
document.addEventListener("DOMContentLoaded", () => {
  function animateCounter(el, target, duration = 1500) {
    let start = 0;
    const step = Math.max(1, Math.ceil(target / (duration / 16))); // ~60fps
    function update() {
      start += step;
      if (start > target) start = target;
      el.textContent = start;
      if (start < target) requestAnimationFrame(update);
    }
    update();
  }

  // Summary Section Counters
  document.querySelectorAll(".summary-count").forEach(counter => {
    const target = +counter.getAttribute("data-target");
    animateCounter(counter, target);
  });

  // Circle Number Counters
  document.querySelectorAll(".count-number").forEach(counter => {
    const target = +counter.closest("svg").querySelector(".circle-progress").dataset.value;
    animateCounter(counter, target);
  });
});


// counter for class wise result
document.addEventListener("DOMContentLoaded", () => {
  const counters = document.querySelectorAll(".count-number");

  counters.forEach(counter => {
    const target = +counter.closest("svg").querySelector(".circle-progress").dataset.value;
    let current = 0;
    const step = Math.ceil(target / 50); // adjust speed

    const update = () => {
      current += step;
      if (current > target) current = target;
      counter.textContent = current;
      if (current < target) requestAnimationFrame(update);
    };
    update();
  });
});

// END==================================================


// // Start Class-wise Student Result Summary (Enhanced Design)

document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll('.class-card');
    cards.forEach(card => {
      const bars = card.querySelectorAll('.progress-bar');
      const numbers = card.querySelectorAll('.progress-number');
      bars.forEach((bar, i) => {
        const target = numbers[i].getAttribute('data-target');
        bar.style.width = target + '%';
        let count = 0;
        const step = Math.ceil(target / 50);
        const interval = setInterval(() => {
          count += step;
          if(count >= target){ count = target; clearInterval(interval); }
          numbers[i].textContent = count;
        }, 30);
      });
    });
  });

  // END==================================================



// ⭐⭐⭐⭐⭐======================== START STUDENT ID

function fillID() {
  document.getElementById("idName").textContent = document.getElementById("fName").value || "—";
  document.getElementById("idRoll").textContent = document.getElementById("fRoll").value || "—";
  document.getElementById("idClass").textContent = document.getElementById("fClass").value || "—";
  document.getElementById("idAddr").textContent = document.getElementById("fAddr").value || "—";
  document.getElementById("idUID").textContent = "STU-" + Math.floor(Math.random() * 9000 + 1000);

  // ✅ Handle file upload (student photo)
  const fileInput = document.getElementById("fPhotoFile");
  const photo = document.getElementById("idPhoto");

  if (fileInput.files && fileInput.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      photo.src = e.target.result;
    };
    reader.readAsDataURL(fileInput.files[0]);
  }
}

// ✅ Print Only the ID Card in Proper Size
function printIDCard() {
  let card = document.getElementById("idCard").outerHTML;

  let win = window.open("", "_blank");
  win.document.write(`
    <html>
      <head>
        <title>Student ID Card</title>
        <style>
          @page {
            size: 86mm 54mm; /* ✅ Standard ID Card Size */
            margin: 0;
          }
          body {
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
          }
          .id-card {
            width: 86mm;
            height: 54mm;
            border: 1px solid #333;
            padding: 5px;
            box-sizing: border-box;
            font-family: Arial, sans-serif;
            font-size: 12px;
          }
          .id-card img.photo {
            width: 32mm;
            height: 38mm;
            object-fit: cover;
          }
        </style>
      </head>
      <body>
        ${card}
      </body>
    </html>
  `);
  win.document.close();
  win.print();
  win.close();
}

function printIDCard() {
  window.print();
}

//--⭐ END========================================================================= 


// ================================Mobile menu toggle (your existing pattern)

document.getElementById('mobile-menu')?.addEventListener('click', function () {
  document.querySelector('.nav-links')?.classList.toggle('active');
});

// Mobile dropdown open/close on tap (desktop still uses hover)
function wireMobileDropdowns() {
  const isMobile = window.matchMedia('(max-width: 768px)').matches;
  document.querySelectorAll('.nav-links .dropdown > a.has-caret').forEach(link => {
    link.onclick = function (e) {
      if (isMobile) {
        e.preventDefault(); // stop jumping to '#'
        const li = this.parentElement;
        li.classList.toggle('open');
      }
    };
  });
}
wireMobileDropdowns();
window.addEventListener('resize', wireMobileDropdowns);

// End Mobile menu toggle Section====================================================

// 

    (function () {
      var open = document.getElementById('openZoom');
      var modalEl = document.getElementById('zoomModal');
      if (!modalEl) return;
      var bsModal;

      function showModal() {
        bsModal = bsModal || new bootstrap.Modal(modalEl);
        bsModal.show();
      }
      if (open) open.addEventListener('click', function (e) { e.preventDefault(); showModal(); });

      var img = document.getElementById('zoomImg');
      var scale = 1, min = 0.5, max = 5;
      var pos = { x: 0, y: 0 }, start = null;

      function apply() {
        img.style.transform = 'translate(' + pos.x + 'px,' + pos.y + 'px) scale(' + scale + ')';
      }
      document.getElementById('zoomIn').onclick = function(){ scale = Math.min(max, scale + 0.25); apply(); };
      document.getElementById('zoomOut').onclick = function(){ scale = Math.max(min, scale - 0.25); apply(); };
      document.getElementById('zoomReset').onclick = function(){ scale = 1; pos = {x:0,y:0}; apply(); };

      img.addEventListener('mousedown', function(e){
        start = { x: e.clientX - pos.x, y: e.clientY - pos.y };
        img.style.cursor = 'grabbing';
      });
      window.addEventListener('mouseup', function(){ start = null; img.style.cursor = 'grab'; });
      window.addEventListener('mousemove', function(e){
        if (!start) return;
        pos.x = e.clientX - start.x; pos.y = e.clientY - start.y; apply();
      });
      img.addEventListener('wheel', function(e){
        e.preventDefault();
        var delta = e.deltaY < 0 ? 0.1 : -0.1;
        scale = Math.min(max, Math.max(min, scale + delta)); apply();
      }, { passive: false });
    })();




// ==== Gallery (images + YouTube) ===========================================
document.addEventListener("DOMContentLoaded", function () {
  const gallery = document.getElementById("glx-gallery");
  const modalEl = document.getElementById("glxModal");
  if (!modalEl) return;

  // Bootstrap modal
  const modal = (window.bootstrap && new bootstrap.Modal(modalEl, { backdrop: true })) || null;

  // UI bits
  const titleEl  = document.getElementById("glxTitle");
  const metaEl   = document.getElementById("glxMeta");

  // Image viewport + tools
  const imgWrap  = document.getElementById("glxImageWrap");
  const imgEl    = document.getElementById("glxImage");
  const btnIn    = document.getElementById("glxZoomIn");
  const btnOut   = document.getElementById("glxZoomOut");
  const btnReset = document.getElementById("glxReset");
  const btnDl    = document.getElementById("glxDownload");

  // Video viewport
  const vidWrap  = document.getElementById("glxVideoWrap");
  const iframe   = document.getElementById("glxIframe");
  const btnOpenYT = document.getElementById("glxOpenYT"); // optional external-open link (if you added one)

  // ---------- YouTube helpers ----------
  function parseYouTubeId(input) {
    if (!input) return "";
    if (/^[\w-]{10,}$/.test(input)) return input; // looks like an ID
    try {
      const u = new URL(input);
      if (u.hostname.includes("youtu.be")) return u.pathname.slice(1);
      const v = u.searchParams.get("v");
      if (v) return v;
      const m = u.pathname.match(/\/(shorts|embed)\/([^/?#]+)/);
      if (m) return m[2];
    } catch (_) {}
    return "";
  }
  function buildYTEmbed(input) {
    const id = parseYouTubeId(input);
    return id ? `https://www.youtube.com/embed/${id}?autoplay=1&rel=0&modestbranding=1` : "";
  }

  // ---------- UI helpers ----------
  function setMeta(title, place, datetime) {
    if (titleEl) titleEl.textContent = title || "";
    if (metaEl)  metaEl.textContent  = [place, datetime].filter(Boolean).join(" · ");
  }
  function showImgTools(show) {
    [btnIn, btnOut, btnReset, btnDl].forEach(b => b && b.classList.toggle("d-none", !show));
  }

  // ---------- Fit / zoom / pan state ----------
  let mode = "image";     // 'image' | 'video'
  let base = 1;           // baseline scale to fit
  let scale = 1;          // current scale
  let pos = { x: 0, y: 0 };
  let dragging = false;
  let dragStart = { x: 0, y: 0 };
  let pendingFit = false;

  function ensureViewportHeight() {
    // Safety net if HTML didn't use vh-100
    if (imgWrap && imgWrap.getBoundingClientRect().height < 40) {
      imgWrap.style.minHeight = "100vh";
    }
    if (vidWrap && vidWrap.getBoundingClientRect().height < 40) {
      vidWrap.style.minHeight = "100vh";
    }
  }

  function applyTransform() {
    if (imgEl) {
      imgEl.style.transform = `translate(${pos.x}px, ${pos.y}px) scale(${scale})`;
    }
  }

  function resetTransform() {
    scale = base;
    pos = { x: 0, y: 0 };
    applyTransform();
  }

  function fitToScreen() {
    if (!imgWrap || !imgEl) return;
    ensureViewportHeight();
    const vw = imgWrap.clientWidth || 1;
    const vh = imgWrap.clientHeight || 1;
    const nw = imgEl.naturalWidth  || vw;
    const nh = imgEl.naturalHeight || vh;
    base = Math.min(vw / nw, vh / nh);
    imgEl.style.maxWidth = "none";
    imgEl.style.maxHeight = "none";
    resetTransform();
    pendingFit = false;
  }

  function zoomAt(fx, fy, factor) {
    if (mode !== "image" || !imgWrap) return;
    const before = scale;
    const next   = Math.min(6, Math.max(base * 0.5, scale * factor));
    const rect   = imgWrap.getBoundingClientRect();
    const cx     = fx - rect.left;
    const cy     = fy - rect.top;
    // keep focal point under cursor
    pos.x = cx - ((cx - pos.x) * (next / before));
    pos.y = cy - ((cy - pos.y) * (next / before));
    scale = next;
    applyTransform();
  }

  // ---------- Openers ----------
  function openImage(src, title, place, datetime) {
    mode = "image";
    if (vidWrap) vidWrap.classList.add("d-none");
    if (iframe)  iframe.src = "";
    if (imgWrap) imgWrap.classList.remove("d-none");
    if (btnOpenYT) btnOpenYT.classList.add("d-none");
    showImgTools(true);

    if (btnDl) {
      btnDl.href = src || "#";
      try { btnDl.download = (src || "").split("/").pop().split("?")[0] || "image"; } catch {}
    }
    setMeta(title, place, datetime);

    if (imgEl) {
      imgEl.onload = () => {
        if (modalEl.classList.contains("show")) {
          requestAnimationFrame(fitToScreen);
        } else {
          pendingFit = true;
        }
      };
      imgEl.src = src || "";
      // If cached, onload may not fire
      if (imgEl.complete) {
        if (modalEl.classList.contains("show")) {
          requestAnimationFrame(fitToScreen);
        } else {
          pendingFit = true;
        }
      }
    }
    modal && modal.show();
  }

  function openVideo(url, title, place, datetime) {
    mode = "video";
    if (imgWrap) imgWrap.classList.add("d-none");
    if (imgEl)   imgEl.src = "";
    if (vidWrap) vidWrap.classList.remove("d-none");
    showImgTools(false);

    const embed = buildYTEmbed(url);
    if (iframe)  iframe.src = embed || "about:blank";

    if (btnOpenYT) {
      const id = parseYouTubeId(url);
      btnOpenYT.href = id ? `https://youtu.be/${id}` : (url || "#");
      btnOpenYT.classList.toggle("d-none", !(id || url));
    }

    setMeta(title, place, datetime);
    modal && modal.show();
  }

  // ---------- Modal lifecycle ----------
  modalEl.addEventListener("shown.bs.modal", () => {
    if (mode === "image" && (pendingFit || scale === 1)) {
      fitToScreen();
    }
  });

  modalEl.addEventListener("hidden.bs.modal", () => {
    if (iframe) iframe.src = "";
    if (imgEl)  imgEl.src = "";
    pendingFit = false;
  });

  // Refit on resize
  window.addEventListener("resize", () => {
    if (modalEl.classList.contains("show") && mode === "image") {
      fitToScreen();
    }
  });

  // ---------- Bind cards ----------
  if (gallery) {
    gallery.querySelectorAll(".glx-card").forEach(card => {
      card.addEventListener("click", (e) => {
        e.preventDefault();
        const kind  = card.dataset.kind;
        const title = card.dataset.title || "";
        const place = card.dataset.place || "";
        const dt    = card.dataset.datetime || "";
        if (kind === "video") {
          const you = card.dataset.video;
          if (you) openVideo(you, title, place, dt);
        } else {
          const src = card.dataset.image || card.querySelector("img")?.src;
          if (src) openImage(src, title, place, dt);
        }
      });
    });
  }

  // ---------- Controls / gestures ----------
  btnIn    && btnIn.addEventListener("click",  () => zoomAt(imgWrap.clientWidth/2, imgWrap.clientHeight/2, 1.2));
  btnOut   && btnOut.addEventListener("click", () => zoomAt(imgWrap.clientWidth/2, imgWrap.clientHeight/2, 1/1.2));
  btnReset && btnReset.addEventListener("click", () => { scale = base; pos = {x:0,y:0}; applyTransform(); });

  if (imgEl) {
    // mouse pan
    imgEl.addEventListener("mousedown", (e) => {
      if (mode !== "image") return;
      dragging = true;
      dragStart = { x: e.clientX - pos.x, y: e.clientY - pos.y };
      imgEl.style.cursor = "grabbing";
    });
    window.addEventListener("mouseup", () => { dragging = false; imgEl.style.cursor = "grab"; });
    window.addEventListener("mousemove", (e) => {
      if (!dragging || mode !== "image") return;
      pos.x = e.clientX - dragStart.x;
      pos.y = e.clientY - dragStart.y;
      applyTransform();
    });
  }

  // wheel zoom under cursor
  imgWrap && imgWrap.addEventListener("wheel", (e) => {
    if (mode !== "image") return;
    e.preventDefault();
    zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? 1.12 : 1/1.12);
  }, { passive: false });

  // double-click toggle zoom
  imgWrap && imgWrap.addEventListener("dblclick", (e) => {
    if (mode !== "image") return;
    e.preventDefault();
    const target = (scale > base * 1.05) ? (base / scale) : (2 / scale);
    zoomAt(e.clientX, e.clientY, target);
  });

  // touch: pinch + pan
  let pinch = null;
  imgWrap && imgWrap.addEventListener("touchstart", (e) => {
    if (mode !== "image") return;
    if (e.touches.length === 2) {
      const [a,b] = e.touches;
      pinch = {
        d: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY),
        cx: (a.clientX + b.clientX) / 2,
        cy: (a.clientY + b.clientY) / 2,
        scale,
        pos: { ...pos }
      };
    } else if (e.touches.length === 1) {
      const t = e.touches[0];
      dragging = true;
      dragStart = { x: t.clientX - pos.x, y: t.clientY - pos.y };
    }
  }, { passive: true });

  imgWrap && imgWrap.addEventListener("touchmove", (e) => {
    if (mode !== "image") return;
    if (e.touches.length === 2 && pinch) {
      e.preventDefault();
      const [a,b] = e.touches;
      const d  = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      const f  = d / (pinch.d || 1);
      const ns = Math.min(6, Math.max(base * 0.5, pinch.scale * f));

      const rect = imgWrap.getBoundingClientRect();
      const cx   = pinch.cx - rect.left;
      const cy   = pinch.cy - rect.top;

      pos.x = cx - ((cx - pinch.pos.x) * (ns / pinch.scale));
      pos.y = cy - ((cy - pinch.pos.y) * (ns / pinch.scale));
      scale = ns;
      applyTransform();
    } else if (e.touches.length === 1 && dragging) {
      const t = e.touches[0];
      pos.x = t.clientX - dragStart.x;
      pos.y = t.clientY - dragStart.y;
      applyTransform();
    }
  }, { passive: false });

  imgWrap && imgWrap.addEventListener("touchend", () => {
    pinch = null;
    dragging = false;
  }, { passive: true });
});



(() => {
  const els = document.querySelectorAll('#academic-calendar .typing-date');

  function type(el, text) {
    el.textContent = '';
    let i = 0;
    const tick = () => {
      if (i <= text.length) {
        el.textContent = text.slice(0, i++);
        requestAnimationFrame(tick);
      }
    };
    requestAnimationFrame(tick);
  }

  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        type(entry.target, entry.target.getAttribute('data-text') || '');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });

  els.forEach(el => io.observe(el));
})();

///////////////////////////////////
//Courses sylabus modal
///////////////////////////////////
// Open syllabus image in LightGallery (zoom + download)
document.addEventListener('click', function (e) {
  const btn = e.target.closest('.js-open-syllabus');
  if (!btn) return;

  e.preventDefault();

  const src = btn.dataset.img;
  const title = btn.dataset.title || 'Syllabus';
  if (!src) {
    console.warn('No data-img on syllabus button.');
    return;
  }

  // Make sure LG is available
  if (typeof window.lightGallery !== 'function') {
    console.error('lightGallery not loaded.');
    return;
  }

  // Use plugins if present
  const plugins = [];
  if (window.lgZoom) plugins.push(window.lgZoom);
  if (window.lgDownload) plugins.push(window.lgDownload);

  // Temporary holder for this one-shot gallery
  const holder = document.createElement('div');
  document.body.appendChild(holder);

  const lg = window.lightGallery(holder, {
    dynamic: true,
    licenseKey: '0000-0000-000-0000', // required param
    plugins,
    closable: true,
    download: true,
    speed: 300,
    backdropDuration: 200,
    dynamicEl: [
      {
        src,
        thumb: src,
        subHtml: `<h4 class="mb-0">${title}</h4>`,
        downloadUrl: src
      }
    ]
  });

  lg.openGallery(0);

  // Clean up when closed
  holder.addEventListener('lgAfterClose', () => {
    lg.destroy(true);
    holder.remove();
  }, { once: true });
});


// --- tiny helpers ---
const setStatus = (type, msg) => {
  const el = $('payment-status'); if (!el) return;
  el.className = `alert alert-${type} py-2 mt-3 mb-0`;
  el.textContent = msg;
};
// ✅ single backslash in the regex literal
const getCSRF = () => (document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/) || [])[1] || '';



  // --- helpers ---
  const setStatus = (type, msg) => {
    const el = $('payment-status'); if (!el) return;
    el.className = `alert alert-${type} py-2 mt-3 mb-0`; el.textContent = msg;
  };
  const getCSRF = () => (document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/) || [])[1] || '';
  const unlock = () => {
    $('submit-btn')?.removeAttribute('disabled');
    $('print-btn')?.removeAttribute('disabled');
    setStatus('success','Payment confirmed ✅');
  };



  // --- PayPal WORKING DEMO (exact style you provided) ---
  // Renders immediately with client-id=test. Uses demo endpoints below.
  paypal.Buttons({
    // Call your server to set up the transaction (DEMO endpoints)
    createOrder: function(data, actions) {
      return fetch('/demo/checkout/api/paypal/order/create/', {
        method: 'post'
      }).then(function(res) {
        return res.json();
      }).then(function(orderData) {
        return orderData.id;
      });
    },

    // Call your server to finalize the transaction (DEMO endpoints)
    onApprove: function(data, actions) {
      return fetch('/demo/checkout/api/paypal/order/' + data.orderID + '/capture/', {
        method: 'post'
      }).then(function(res) {
        return res.json();
      }).then(function(orderData) {
        // If there’s a recoverable decline
        var errorDetail = Array.isArray(orderData.details) && orderData.details[0];
        if (errorDetail && errorDetail.issue === 'INSTRUMENT_DECLINED') {
          return actions.restart();
        }
        if (errorDetail) {
          var msg = 'Sorry, your transaction could not be processed.';
          if (errorDetail.description) msg += '\n\n' + errorDetail.description;
          if (orderData.debug_id) msg += ' (' + orderData.debug_id + ')';
          return alert(msg);
        }

        // Successful capture!
        console.log('Capture result', orderData);
        unlock();
      });
    }
  }).render('#paypal-button-container');

  // If returning from a provider with ?paid=1
  (function(){
    const q = new URLSearchParams(location.search);
    if (q.get('paid') === '1') unlock();
  })();




  (function () {
    // Add bootstrap classes to inputs/selects/textareas that lack them





      // checkboxes: visually toggle fee rows (demo behavior, implement real calc)
      document.getElementById('optBus')?.addEventListener('change', (e) => {
        document.querySelector('[data-fee-bus]').textContent = e.target.checked ? '৳ 500' : '৳ 0';
        // update total (simple parse)
        updateTotal();
      });
      document.getElementById('optHostel')?.addEventListener('change', (e) => {
        document.querySelector('[data-fee-hostel]').textContent = e.target.checked ? '৳ 1500' : '৳ 0';
        updateTotal();
      });
      document.getElementById('optMarksheet')?.addEventListener('change', (e) => {
        document.querySelector('[data-fee-marksheet]').textContent = e.target.checked ? '৳ 200' : '৳ 0';
        updateTotal();
      });

      function parseAmount(text) {
        return Number(String(text).replace(/[^\d.-]/g,'') || 0);
      }
      function updateTotal() {
        const admission = parseAmount(document.querySelector('[data-fee-admission]').textContent);
        const tuition = parseAmount(document.querySelector('[data-fee-tuition]').textContent);
        const exam = parseAmount(document.querySelector('[data-fee-exam]').textContent);
        const bus = parseAmount(document.querySelector('[data-fee-bus]').textContent);
        const hostel = parseAmount(document.querySelector('[data-fee-hostel]').textContent);
        const marksheet = parseAmount(document.querySelector('[data-fee-marksheet]').textContent);
        const total = admission + tuition + exam + bus + hostel + marksheet;
        document.querySelector('[data-fee-total]').textContent = '৳ ' + total;
      }
      // initial total calc
      updateTotal();
    });
  })();



// ---- helpers (define ONCE) ----
const getCSRF = () =>
  (document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/) || [])[1] || "";

function setStatus(type, msg) {
  const el = document.getElementById('payment-status');
  if (!el) return;
  el.className = `alert alert-${type} py-2 mt-3 mb-0`;
  el.textContent = msg;
}



document.getElementById('btnPrint')?.addEventListener('click', () => window.print());
