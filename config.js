// Edit this file only. index.html, style.css and script.js read everything from here.
window.SITE_CONFIG = {
  name: "Manikanta Nandam",
  initials: "MN",
  title: "Software Engineer",
  intro: "I build reliable mobile and web apps. Replace this line with a short intro about you.",
  photo: "images/profile.svg",        // put your photo in images/ and change this path
  resume: "resume.pdf",               // set to "" to hide the Download Resume button

  contact: {
    email: "nanirocks125@gmail.com",
    phone: "+910000000000",           // with country code, used for the Call button
    whatsapp: "910000000000",         // digits only: country code + number, no + or spaces. "" hides WhatsApp
    whatsappMessage: "Hi Manikanta, I found your portfolio and would like to connect.",
    emailSubject: "Hello from your portfolio"
  },

  social: {
    github: "https://github.com/manikantanandam",
    linkedin: "https://www.linkedin.com/in/your-handle"   // "" hides the link
  },

  about: [
    "Write 2-3 sentences: your current role, education, and what you enjoy building."
  ],

  skills: [
    { title: "Languages & Frameworks", items: ["Swift", "SwiftUI", "Kotlin"] },
    { title: "Technologies", items: ["SQLite", "Firebase"] },
    { title: "Tools", items: ["Git", "GitHub", "Xcode"] },
    { title: "Soft Skills", items: ["Communication", "Problem solving"] }
  ],

  experience: [
    {
      role: "Role",
      company: "Company",
      period: "Start - Present",
      points: ["Achievement or responsibility with measurable impact.", "Another achievement."]
    }
  ],

  projects: [
    {
      name: "Apoorva",
      description: "Offline-first POS and business management app built with Swift, SwiftUI and Skip.",
      tags: ["Swift", "SwiftUI", "Firebase"],
      link: "https://github.com/manikantanandam"
    }
  ]
};
