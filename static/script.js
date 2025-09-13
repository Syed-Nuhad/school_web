  

// ⭐ END Initialize AOS ==============================================================================


// ⭐⭐⭐⭐⭐============================= START: Navigation Menu Script 

// ⭐ ======= START: Select Elements 

const mobileMenu = document.getElementById("mobile-menu");
const navLinks = document.querySelector(".nav-links");

// ⭐ END: Select Elements ==============================================================================



// ⭐========================= START: Toggle Mobile Menu 


mobileMenu.addEventListener("click", () => {
  navLinks.classList.toggle("active");
});
// ⭐ END Toggle Mobile Menu =============================================================================

// ⭐ END Navigation Menu Script =========================================================================



  // ⭐⭐⭐⭐⭐ =============================== START: Banner Slider Script 

// ⭐ ================== START: Select Elements 

const slides = document.querySelectorAll(".slide");
const prevBtn = document.querySelector(".prev");
const nextBtn = document.querySelector(".next");
const dotsContainer = document.querySelector(".dots");
// ===== END: Select Elements ===============================================================================

let currentIndex = 0;

// ⭐============================= START: Create Dots Dynamically 

slides.forEach((_, index) => {
  const dot = document.createElement("span");
  if (index === 0) dot.classList.add("active");
  dot.addEventListener("click", () => showSlide(index));
  dotsContainer.appendChild(dot);
});
const dots = document.querySelectorAll(".dots span");

// ⭐ END Create Dots Dynamically ======================================================================




// ⭐⭐⭐⭐⭐============================= START: Show Specific Slide 

function showSlide(index) {
  slides.forEach(slide => slide.classList.remove("active"));
  dots.forEach(dot => dot.classList.remove("active"));

  slides[index].classList.add("active");
  dots[index].classList.add("active");

  currentIndex = index;
}


// ⭐ END Show Specific Slide =============================================================================


// ⭐⭐⭐⭐⭐===================== START: Next & Previous Slide Functions 

function nextSlide() {
  currentIndex = (currentIndex + 1) % slides.length;
  showSlide(currentIndex);
}

function prevSlide() {
  currentIndex = (currentIndex - 1 + slides.length) % slides.length;
  showSlide(currentIndex);
}
// ⭐END  Next & Previous Slide Functions ==============================================================

// ⭐⭐⭐⭐⭐ ====================== START: Event Listeners 
prevBtn.addEventListener("click", prevSlide);

// ⭐ END: Event Listeners ============================================================================


// ⭐⭐⭐⭐⭐======================== START: Auto Slide Every 5 Seconds 

setInterval(nextSlide, 5000);

// ⭐ END  ⭐ Auto Slide Every 5 Seconds =============================================================



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




  // ⭐⭐⭐⭐⭐=========Start : Online Admission Form Section. Smooth scroll if nav links jump to this form
  
// Use jsPDF from CDN to generate PDF on submit success
  // const { jsPDF } = window.jspdf;

  // ⭐⭐⭐⭐⭐ Start : Online Admission Form Payment Simulation, Feedback, and PDF Generation

  // Payment confirmation simulation & UI update
  document.getElementById('confirm-payment-btn').addEventListener('click', () => {
    const paymentMethod = document.getElementById('payment-method').value;
    const paymentStatus = document.getElementById('payment-status');
    const submitBtn = document.getElementById('submit-btn');
    const printBtn = document.getElementById('print-btn');

    if (!paymentMethod) {
      paymentStatus.className = 'alert alert-danger py-2';
      paymentStatus.textContent = 'Please select a payment method before confirming.';
      submitBtn.disabled = true;
      printBtn.disabled = true;
      return;
    }

    // For demo, randomly decide success or failure
    const success = Math.random() > 0.3; // 70% chance success

    if(success){
      paymentStatus.className = 'alert alert-success py-2';
      paymentStatus.textContent = 'Payment successful, please submit the form.';
      submitBtn.disabled = false;
      printBtn.disabled = false;
    } else {
      paymentStatus.className = 'alert alert-danger py-2';
      paymentStatus.textContent = 'Payment not paid, please pay first and submit later.';
      submitBtn.disabled = true;
      printBtn.disabled = true;
    }
  });

  // Submit form handler (you can add real form submission here)
  document.querySelector('#admission-form form').addEventListener('submit', e => {
    e.preventDefault();
    alert('Form submitted! You will receive a PDF copy via email.');
  });

  // Print button handler
  document.getElementById('print-btn').addEventListener('click', () => {
    window.print();
  });


  // Optionally, add form submit and download PDF logic here
  // ⭐ End : Online Admission Form Section. Smooth scroll if nav links jump to this form =========================




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

const SYLLABUS_DATA = {
  "HSC – Science": {
    overview: "This syllabus covers core science subjects with emphasis on lab work, problem solving, and exam preparation.",
    modules: [
      ["Physics: Mechanics", "Kinematics, Dynamics, Work-Energy, Power"],
      ["Physics: Waves & Optics", "Wave motion, Sound, Mirrors, Lenses"],
      ["Physics: Electricity", "Current, Circuits, EMF, Kirchhoff's laws"],
      ["Chemistry: Physical", "Mole concept, Thermodynamics, Kinetics"],
      ["Chemistry: Inorganic", "Periodic table, Bonding, Coordination"],
      ["Chemistry: Organic", "Hydrocarbons, Functional groups, Reactions"],
      ["Mathematics: Algebra", "Sets, Functions, Quadratics, Progressions"],
      ["Mathematics: Calculus", "Limits, Derivatives, Basic Integrals"],
      ["Biology: Cell Biology", "Cell structure, Transport, Division"],
      ["Biology: Genetics", "Mendelian genetics, DNA, Gene expression"],
      // duplicate some rows to force multiple pages
      ["Lab Work", "Physics/Chemistry/Biology practicals & reports"],
      ["Project", "Science fair participation & presentation"],
      ["Revision", "Mock tests, question banks, past papers"],
      ["Soft Skills", "Time management, presentation, note-taking"],
      ["ICT Basics", "Spreadsheets, Presentations, Internet safety"],
      ["Seminars", "Guest lectures from academicians"],
      ["Career Guidance", "Engineering/Medical admissions roadmap"],
      ["Ethics", "Academic integrity & lab safety"],
      ["Field Visit", "Local science museum/industry visit"],
      ["Assessment", "Unit tests, midterms, finals"]
    ]
  },
  "HSC – Commerce": {
    overview: "Focus on Accounting, Business Studies, and Economics with practical projects.",
    modules: [
      ["Accounting I", "Journal, Ledger, Trial Balance"],
      ["Accounting II", "Financial statements, Ratios"],
      ["Business Studies", "Management, Marketing, HRM"],
      ["Economics I", "Microeconomics basics"],
      ["Economics II", "Macroeconomics basics"],
      ["ICT for Commerce", "Spreadsheets & presentations"],
      ["Entrepreneurship", "Business plan & pitching"],
      ["Project", "Case study on a local business"],
      ["Assessment", "Unit tests, midterms, finals"]
    ]
  },
  "HSC – Arts": {
    overview: "Languages, Social Sciences, and Humanities with emphasis on reading & research.",
    modules: [
      ["Bangla Literature", "Poetry, drama, prose"],
      ["English", "Grammar, composition, comprehension"],
      ["History", "Regional & world history themes"],
      ["Civics", "Governance, constitution, rights"],
      ["Geography", "Physical & human geography"],
      ["Sociology", "Society & culture basics"],
      ["Research Skills", "Referencing & reports"],
      ["Debate Club", "Public speaking & debating"],
      ["Assessment", "Unit tests, midterms, finals"]
    ]
  }
};

// ---- Generate PDF (A4, multi-page) ----
function generateSyllabusPdf(courseTitle) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });

  const course = SYLLABUS_DATA[courseTitle] || {
    overview: "Detailed syllabus will be provided by the department.",
    modules: [["Overview", "Content will be announced soon."]]
  };

  const margin = 15;
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();

  // Header & footer for every page
  const drawHeader = () => {
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.text("College Syllabus", margin, 14);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);
    doc.text(courseTitle, margin, 21);
  };

  const applyFooters = () => {
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(10);
      doc.text(`Page ${i} of ${pageCount}`, pageW - margin, pageH - 8, { align: "right" });
    }
  };

  // First page body
  drawHeader();
  doc.setFontSize(11);
  doc.text("Overview:", margin, 32);
  doc.setFont("helvetica", "normal");
  doc.text(course.overview, margin, 39, { maxWidth: pageW - margin * 2 });

  // Modules table (autoTable handles page breaks)
  const tableStartY = 52;
  doc.autoTable({
    startY: tableStartY,
    margin: { left: margin, right: margin },
    headStyles: { fillColor: [13, 110, 253] },  // Bootstrap primary
    styles: { fontSize: 10, cellPadding: 3 },
    head: [["Module", "Key Topics"]],
    body: course.modules,
    didDrawPage: () => {
      drawHeader();
    }
  });

  applyFooters();
  const filename = `${courseTitle.replace(/\s+/g, "_")}_Syllabus.pdf`;
  doc.save(filename);
}

// ---- Wire the buttons ----
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('#academics .syllabus-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const card = btn.closest('.card');
      const title = card.querySelector('.card-title')?.textContent?.trim() || "Syllabus";
      generateSyllabusPdf(title);
    });
  });
});


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

// ---------------------------------------------------------------
//   Search submit
//----------------------------------------------------------------
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const name = form.name.value.trim().toLowerCase();
  const roll = form.roll.value.trim();
  const cls = form.class.value;
  const section = form.section.value;

  const found = students.find((student) => {
    return (
      (name === "" || student.name.toLowerCase().includes(name)) &&
      (roll === "" || student.roll === roll) &&
      (cls === "" || student.class === cls) &&
      (section === "" || student.section === section)
    );
  });

  if (!found) {
    alert("No student found with the given details.");
    marksheet.style.display = "none";
    currentStudent = null;
    return;
  }

  currentStudent = found;
  showMarksheet(found);
});

// ---------------------------------------------------------------
//   Print + PDF (Letter size, with background + logo)
//----------------------------------------------------------------
printBtn.addEventListener("click", () => window.print());

downloadBtn.addEventListener("click", async () => {
  if (!currentStudent) return alert("Please search for a student first.");

  const { jsPDF } = window.jspdf || {};
  if (!jsPDF) {
    alert("jsPDF not loaded. Please include jsPDF and jspdf-autotable.");
    return;
  }
  const doc = new jsPDF({ orientation: "p", unit: "mm", format: "letter" });

  if (typeof doc.autoTable !== "function") {
    alert("jsPDF AutoTable plugin not loaded. Please include it after jsPDF.");
    return;
  }

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();

  // Prepare assets
  const collegeName = (document.getElementById("collegeName")?.textContent || "College Name").trim();
  const examName = (document.getElementById("examName")?.textContent || "Examination").trim();
  const logoImgEl = marksheet.querySelector("img");
  const logoDataURL = logoImgEl ? await loadImageAsDataURL(logoImgEl) : null;
  // Use the same background you use in CSS for consistency
  const bgDataURL = await loadImageAsDataURL("./img/background/marksheet-bg.png");

  // Page frame + background + header on every page
  const drawFrameAndHeader = () => {
    // Background image stretched to page
    if (bgDataURL) {
      doc.addImage(bgDataURL, "PNG", 0, 0, pageWidth, pageHeight, "", "FAST");
    }
    // Decorative frame
    doc.setDrawColor(0, 0, 0); doc.setLineWidth(0.6);
    doc.rect(8, 8, pageWidth - 16, pageHeight - 16);

    // Header
    if (logoDataURL) doc.addImage(logoDataURL, "PNG", 12, 12, 20, 20);
    doc.setFont(undefined, "bold"); doc.setFontSize(16);
    doc.text(collegeName, pageWidth / 2, 18, { align: "center" });
    doc.setFont(undefined, "normal"); doc.setFontSize(12);
    doc.text(examName, pageWidth / 2, 24, { align: "center" });
    // Divider
    doc.setLineWidth(0.3);
    doc.line(10, 32, pageWidth - 10, 32);
  };

  drawFrameAndHeader();

  // Student info
  doc.setFontSize(11);
  let y = 38;
  doc.text(`Name: ${currentStudent.name}`, 12, y);
  doc.text(`Roll No: ${currentStudent.roll}`, pageWidth / 2, y);
  y += 6;
  doc.text(`Class: ${currentStudent.class}`, 12, y);
  doc.text(`Section: ${currentStudent.section}`, pageWidth / 2, y);

  // Build table rows (repeat position column)
  const totalFull = currentStudent.marks.reduce((s, m) => s + Number(m.full || 0), 0);
  const totalObt = currentStudent.marks.reduce((s, m) => s + Number(m.obtained || 0), 0);
  const position = rankInSection(currentStudent, students);
  const finalGrade = gradeFromScore(totalObt, totalFull);

  const tableBody = currentStudent.marks.map((m) => [
    m.subject,
    String(m.full),
    String(m.obtained),
    gradeFromScore(m.obtained, m.full),
    String(position)
  ]);

  doc.autoTable({
    head: [["Subject", "Full Marks", "Marks Obtained", "Grade Obtained", "Position"]],
    body: tableBody,
    foot: [["Total", String(totalFull), String(totalObt), String(finalGrade), String(position)]],
    startY: 50,
    theme: "grid",
    headStyles: { fillColor: [13, 110, 253], textColor: 255 },
    footStyles: { fillColor: [220, 220, 220], textColor: 0, fontStyle: "bold" },
    styles: { fontSize: 11, cellPadding: 2 },
    margin: { left: 12, right: 12 },
    didDrawPage: drawFrameAndHeader
  });

  // Attendance + signatures
  let afterTableY = doc.lastAutoTable.finalY + 8;
  const presentText = currentStudent.attendance?.present ?? (daysPresentEl?.textContent || "");
  const absentText  = currentStudent.attendance?.absent  ?? (daysAbsentEl?.textContent  || "");
  if (presentText || absentText) {
    doc.setFontSize(11);
    doc.text(`Days Present: ${presentText || "—"}   |   Days Absent: ${absentText || "—"}`, 12, afterTableY);
    afterTableY += 10;
  }
  const sigY = Math.min(afterTableY + 10, pageHeight - 30);
  const leftX = 20;
  const rightX = pageWidth - 20;
  doc.line(leftX, sigY, leftX + 60, sigY);
  doc.line(rightX - 60, sigY, rightX, sigY);
  doc.setFontSize(10);
  doc.text("Parent's Signature", leftX, sigY + 6);
  doc.text("Class Teacher's Signature", rightX - 60, sigY + 6);

  doc.save(`Marksheet_${currentStudent.name.replace(/\s+/g, "_")}.pdf`);
});

// ⭐ End =======================================================================


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

// Filter functionality
document.getElementById('filterClass').addEventListener('change', applyFilters);
document.getElementById('filterSection').addEventListener('change', applyFilters);
document.getElementById('viewAllBtn').addEventListener('click', () => {
  document.getElementById('filterClass').value = '';
  document.getElementById('filterSection').value = '';
  loadMembers(currentCategory, 1);
});

function applyFilters() {
  const classFilter = document.getElementById('filterClass').value;
  const sectionFilter = document.getElementById('filterSection').value;
  const membersContainer = document.getElementById('membersContainer');
  membersContainer.innerHTML = '';

  const members = membersData[currentCategory];
  const filteredMembers = members.filter(member => {
    let matchClass = classFilter ? member.post === classFilter : true;
    let matchSection = sectionFilter ? (member.section || '') === sectionFilter : true;
    return matchClass && matchSection;
  });

  filteredMembers.forEach(member => {
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
}

// ⭐End Dashboard Section JS ============================================================




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

document.addEventListener('DOMContentLoaded', function() {
  // Element references
  const modalEl = document.getElementById('galleryModal');
  const imgWrap = document.getElementById('gmImageWrap');
  const imgEl   = document.getElementById('gmImage');
  const vidWrap = document.getElementById('gmVideoWrap');
  const iframe  = document.getElementById('gmIframe');
  const titleEl = document.getElementById('gmTitle');
  const metaEl  = document.getElementById('gmMeta');
  const btnClose = document.getElementById('gmClose');
  const btnZoomIn  = document.getElementById('gmZoomIn');
  const btnZoomOut = document.getElementById('gmZoomOut');
  const btnReset   = document.getElementById('gmReset');
  const btnDownload= document.getElementById('gmDownload');

  // Helper: convert YouTube URLs to embed URL
  function toEmbed(url) {
    if (!url) return '';
    try {
      const u = new URL(url);
      // Short link youtu.be/ID
      if (u.hostname.includes('youtu.be')) {
        const videoId = u.pathname.slice(1);
        return `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
      }
      // Long link youtube.com/watch?v=ID
      const v = u.searchParams.get('v');
      if (v) {
        return `https://www.youtube.com/embed/${v}?autoplay=1&rel=0`;
      }
      // Shorts link youtube.com/shorts/ID
      const m = u.pathname.match(/\/shorts\/([^\/]+)/);
      if (m) {
        return `https://www.youtube.com/embed/${m[1]}?autoplay=1&rel=0`;
      }
      // If already an embed link or other URL, append autoplay=1 if not present
      return url.includes('autoplay=') ? url :
             url + (url.includes('?') ? '&' : '?') + 'autoplay=1&rel=0';
    } catch {
      return url;
    }
  }

  // Open image in modal
  function openImage({ src, title, meta }) {
    // Show image container, hide video
    imgWrap.style.display = '';
    vidWrap.style.display = 'none';
    iframe.src = '';  // stop any previously playing video
    // Set image source and text
    imgEl.src = src;
    titleEl.textContent = title || 'Image';
    metaEl.textContent  = meta || '';
    // Prepare download link
    btnDownload.href = src;
    try {
      // Set download filename from URL
      btnDownload.download = src.split('/').pop().split('?')[0] || 'image';
    } catch {}
    // Reset zoom/pan to default
    resetTransform();
    // Show zoom/download controls for images
    btnZoomIn.style.display = '';
    btnZoomOut.style.display = '';
    btnReset.style.display   = '';
    btnDownload.style.display= '';
    // Display the modal overlay
    modalEl.classList.add('open');
  }

  // Open video in modal
  function openVideo({ url, title, meta }) {
    // Show video container, hide image
    vidWrap.style.display = '';
    imgWrap.style.display = 'none';
    // Set video iframe source (converted to embed URL with autoplay)
    iframe.src = toEmbed(url);
    titleEl.textContent = title || 'Video';
    metaEl.textContent  = meta || '';
    // Hide image-specific controls
    btnZoomIn.style.display = 'none';
    btnZoomOut.style.display = 'none';
    btnReset.style.display   = 'none';
    btnDownload.style.display= 'none';
    // Display the modal overlay
    modalEl.classList.add('open');
  }

  // Close the modal
  function closeModal() {
    modalEl.classList.remove('open');
    iframe.src = '';             // stop video
    imgEl.src = '';              // release image
    // (Zoom state reset when opening images next time)
  }

  // Click handlers for each gallery item
  document.querySelectorAll('.gallery-item').forEach(card => {
    card.addEventListener('click', e => {
      e.preventDefault();
      const kind  = card.dataset.kind;
      const title = card.dataset.title || '';
      const meta  = [card.dataset.place, card.dataset.datetime].filter(Boolean).join(' · ');
      if (kind === 'video') {
        const url = card.dataset.video;
        if (url) openVideo({ url, title, meta });
      } else {
        // kind "image"
        const src = card.dataset.image || card.querySelector('img')?.src;
        if (src) openImage({ src, title, meta });
      }
    });
  });

  // Zoom and pan functionality for images
  let scale = 1;
  let pos = { x: 0, y: 0 };
  let isDragging = false;
  let dragStart = { x: 0, y: 0 };

  function applyTransform() {
    imgEl.style.transform = `translate(${pos.x}px, ${pos.y}px) scale(${scale})`;
  }
  function resetTransform() {
    scale = 1;
    pos = { x: 0, y: 0 };
    applyTransform();
  }

  // Zoom control buttons
  btnZoomIn.addEventListener('click', () => {
    scale = Math.min(5, scale + 0.25);
    applyTransform();
  });
  btnZoomOut.addEventListener('click', () => {
    scale = Math.max(0.5, scale - 0.25);
    applyTransform();
  });
  btnReset.addEventListener('click', () => {
    resetTransform();
  });

  // Drag to pan image
  imgEl.addEventListener('mousedown', e => {
    isDragging = true;
    dragStart = { x: e.clientX - pos.x, y: e.clientY - pos.y };
    imgEl.style.cursor = 'grabbing';
  });
  window.addEventListener('mouseup', () => {
    isDragging = false;
    imgEl.style.cursor = 'grab';
  });
  window.addEventListener('mousemove', e => {
    if (!isDragging) return;
    pos.x = e.clientX - dragStart.x;
    pos.y = e.clientY - dragStart.y;
    applyTransform();
  });

  // Zoom with mouse wheel
  imgEl.addEventListener('wheel', e => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.1 : -0.1;
    scale = Math.min(5, Math.max(0.5, scale + delta));
    applyTransform();
  }, { passive: false });

  // Close modal on close button, backdrop click, or Escape key
  btnClose.addEventListener('click', closeModal);
  modalEl.addEventListener('click', e => {
    if (e.target === modalEl) {
      closeModal();
    }
  });
  window.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeModal();
    }
  });
});