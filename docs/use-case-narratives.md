# Use Case Narratives - CPSC 49200

## Team and Project

- **Project Name** - FixIt – Report It. Track It. Get It Fixed. (A Community Problem Reporting & Tracking System)
- **Team Name** - Team FixIt (individual capstone project)
- **Team Members**
  - Anjaliben Ghanshyambhai Valand, AnjalibenGhanshyam@lewisu.edu, skilled in front-end development (HTML5, CSS3, JavaScript, React), back-end development and REST APIs, database design (PostgreSQL), and full-stack web application development, testing, and deployment.

The selected implementation stack is React for the frontend, Python with Flask for the backend, and PostgreSQL for data storage. Backend tests will use pytest and the Flask test client.

## Use case narratives

We now present the features of the minimum viable product (MVP) version
of this project as a set of use case narratives. Each use case narrative
starts with a title that identifies the user and how they will use the
system. Then the narrative will describe the details of that interaction,
including exceptional circumstances that may arise. If two different kinds
of roles exercise a particular feature differently, those are presented
here as two use case narratives.

FixIt has three actors:

- **Resident** – a regular user (an apartment resident, college student or staff member, or neighborhood resident) who reports problems and tracks them.
- **Administrator** – a community manager or staff member who reviews, assigns, and updates reports.
- **System** – the FixIt application itself, which carries out automatic behind-the-scenes services such as protecting credentials, enforcing permissions, and recording history.

We will list these use case narratives as a set of checkboxes, since
they are features we will check off as we complete their implementation.

- [ ] 1. **Resident creates an account.**
  A new visitor arrives at the FixIt home page and clicks **Sign Up**. The
  registration form asks for their full name, email address, a password, and a
  password confirmation. As the resident types, the form shows the password
  rules (at least 8 characters, containing at least one letter and one
  number). When the resident clicks **Create Account**, the system validates the
  input, creates a new account with the role *Resident*, signs the resident in,
  and takes them to their empty **My Reports** dashboard with a welcome message
  and a large **Report a Problem** button. Residents cannot choose their own
  role; every self-registered account is a Resident account.
  *Exceptional circumstances:*
  - If any required field is empty, the field is outlined in red and a message such as "Email is required" appears beneath it; the form is not submitted.
  - If the email address is not in a valid format, the resident sees "Please enter a valid email address."
  - If the password does not meet the rules, or the two password fields do not match, the resident sees a specific message explaining which rule failed.
  - If an account with that email already exists, the system displays "An account with this email already exists. Please log in instead," with a link to the login page. Previously typed values (except passwords) stay in the form so the resident does not have to retype them.
  - If the server cannot be reached, the resident sees "We couldn't create your account right now. Please try again in a moment," and no partial account is created.

- [ ] 2. **Resident logs in.**
  A returning resident clicks **Log In**, enters their email address and
  password, and clicks **Log In**. The system verifies the credentials, starts a
  secure session, and opens the resident's **My Reports** dashboard. The
  navigation bar shows the resident's name, a **Report a Problem** link, a
  **My Reports** link, and a **Log Out** button. Residents never see any
  administrator menu items.
  *Exceptional circumstances:*
  - If the email or password is wrong, the system shows the generic message "Incorrect email or password" without revealing which one was wrong, so attackers cannot discover which emails are registered. The password field is cleared and the email field is kept.
  - After five consecutive failed attempts for the same account, the system temporarily blocks further login attempts for 15 minutes and tells the user "Too many failed attempts. Please try again later."
  - If either field is blank, the form shows "Email and password are required" and does not submit.
  - If a logged-out resident tries to open a protected page directly (for example, by bookmarking **My Reports**), they are redirected to the login page and, after logging in, are returned to the page they originally requested.

- [ ] 3. **Administrator logs in to the administrator dashboard.**
  Administrators use the same login page as residents, but their accounts are
  created with the *Administrator* role ahead of time (they cannot be created
  through public sign-up). When an administrator enters valid credentials, the
  system recognizes the role and opens the **Administrator Dashboard** instead
  of **My Reports**. The navigation bar for administrators shows **Dashboard**,
  **All Reports**, and **Log Out**, and a small "Admin" badge next to their name
  so they always know they are using elevated permissions.
  *Exceptional circumstances:*
  - Incorrect credentials, blank fields, and repeated failed attempts are handled exactly as in the resident login (generic error message, temporary lockout after five failures).
  - If an administrator's account has been deactivated, the login is refused with "This account is not active. Please contact your community manager."

- [ ] 4. **User logs out.**
  Any logged-in resident or administrator can click **Log Out** in the
  navigation bar at any time. The system ends the session on the server,
  clears the session token from the browser, and returns the user to the home
  page with the message "You have been logged out." Pressing the browser's Back
  button after logging out does not reveal protected pages; any attempt to
  access them redirects to the login page.
  *Exceptional circumstances:*
  - If a session expires because the user has been inactive for a long period (for example, 60 minutes), the system automatically logs the user out. The next time they try to perform an action, they see "Your session has expired. Please log in again," and any report form they were filling in is not silently lost—the user is warned before being redirected.

- [ ] 5. **Resident reports a community problem.**
  A resident notices a broken hallway light and, from their phone or computer,
  clicks **Report a Problem**. A short, single-page form appears with these fields:
  - **Title** – a short summary, such as "Hallway light out on 3rd floor" (required, up to 100 characters).
  - **Category** – a drop-down list of predefined categories: Lighting, Roads & Sidewalks, Trash & Recycling, Plumbing, Equipment & Facilities, Safety, and Other (required).
  - **Location** – a text field for a building, address, room number, or landmark, such as "Building B, 3rd floor, near Unit 312" (required).
  - **Description** – additional details about the problem (optional, up to 1,000 characters, with a character counter).
  - **Photo** – an optional photo (see use case 6).

  When the resident clicks **Submit Report**, the system validates the form,
  saves the report linked to the resident's account, stamps it with the current
  date and time, assigns a unique report number (for example, *#1042*), and sets
  its status to **Reported**. The resident sees a confirmation screen that reads
  "Thank you! Your report #1042 has been submitted," with buttons to **View
  Report** or **Report Another Problem**. The new report immediately appears at
  the top of the resident's dashboard and in the administrators' list of new reports.
  *Exceptional circumstances:*
  - If the title, category, or location is missing, the form highlights the missing fields and displays a message such as "Please choose a category," without clearing anything the resident already entered.
  - If the title or description exceeds the length limit, the counter turns red and the form will not submit until the text is shortened.
  - If the resident's problem doesn't fit any category, they choose **Other** and explain in the description.
  - If the submission fails because of a network or server error, the form remains filled in and shows "Your report could not be submitted. Please try again," so no work is lost.
  - Double-clicking **Submit Report** does not create duplicate reports; the button is disabled while the submission is being processed.

- [ ] 6. **Resident attaches a photo to a report.**
  While filling out the report form, the resident taps **Add Photo**. On a
  phone, they can take a new picture with the camera or choose one from their
  gallery; on a computer, a file picker opens. Once a photo is selected, a
  thumbnail preview appears on the form with a **Remove** option so the resident
  can change their mind before submitting. When the report is submitted, the
  system uploads the image to file storage, saves a reference to it with the
  report, and the photo is shown on the report details page for both the
  resident and administrators. Only one photo per report is supported in the MVP.
  *Exceptional circumstances:*
  - If the file is not an accepted image type (JPEG, PNG, or WEBP), the resident sees "Only JPG, PNG, or WEBP images can be uploaded," and the file is rejected.
  - If the image is larger than 5 MB, the resident sees "This photo is too large (maximum 5 MB). Please choose a smaller image."
  - If the photo upload fails while the rest of the report is valid, the resident is told "The photo could not be uploaded," and can retry the upload or submit the report without a photo.
  - Because a photo is optional, residents can always submit a report without one.

- [ ] 7. **Resident views and tracks their submitted reports on the My Reports dashboard.**
  After logging in, the resident lands on **My Reports**, a list of every
  problem they have submitted, newest first. Each item shows the report number,
  title, category, location, date submitted, and a color-coded status badge:
  gray for **Reported**, blue for **Assigned**, orange for **In Progress**, and
  green for **Resolved**. At the top of the page, summary counts show how many of
  the resident's reports are open and how many are resolved. The resident can
  quickly narrow the list with simple tabs for **All**, **Open**, and **Resolved**.
  On a phone, the list displays as stacked cards; on a desktop, it displays as a
  table. Clicking any report opens its details (use case 8). Residents only ever
  see their own reports on this page.
  *Exceptional circumstances:*
  - If the resident has not submitted any reports yet, the dashboard shows a friendly empty state: "You haven't reported any problems yet," with a **Report a Problem** button.
  - If the reports cannot be loaded because of a server or network problem, the page shows "We couldn't load your reports. Please refresh the page," instead of an empty list that might be mistaken for "no reports."

- [ ] 8. **Resident views the details and progress history of one of their reports.**
  From **My Reports**, the resident clicks a report and the **Report Details**
  page opens. It shows the title, report number, category, location, full
  description, the attached photo (which can be tapped to enlarge), the date
  submitted, and the current status badge. Below that is a **Progress Timeline**
  that lists each status change in order, for example:
  "Reported – Oct 3, 9:14 AM" → "Assigned – Oct 3, 2:30 PM" →
  "In Progress – Oct 4, 10:05 AM" → "Resolved – Oct 4, 4:45 PM," along with any
  short note the administrator added (such as "Bulb replaced"). The resident can
  also see whether the problem has been assigned to someone, giving them clear
  evidence that their report is being handled. Residents can view, but not
  change, the status or assignment.
  *Exceptional circumstances:*
  - If a resident tries to open a report that belongs to another user (for example, by changing the report number in the URL), the system refuses with "You do not have permission to view this report," and the report's contents are never sent to the browser.
  - If the report number does not exist, the resident sees "Report not found," with a link back to **My Reports**.
  - If the photo file cannot be loaded, a placeholder reading "Photo unavailable" is shown and the rest of the report still displays.

- [ ] 9. **Administrator reviews all reports on the administrator dashboard.**
  After logging in, the administrator sees the **Administrator Dashboard**. At
  the top are summary tiles with the number of reports in each status (for
  example, *8 Reported, 5 Assigned, 3 In Progress, 41 Resolved*), and a
  highlighted **Needs Attention** count showing open reports that are still
  unassigned or that have been open for more than seven days. A tile listing the
  most frequently reported categories helps the administrator see which kinds of
  problems are most common. Below the tiles is a table of all reports from every
  resident, showing report number, title, category, location, submitter's name,
  date submitted, assigned person, and status. The table is sorted by newest
  first by default, and the administrator can click column headers to sort by
  date, status, or category. Clicking a row opens the administrator's version of
  the report details page (use case 11).
  *Exceptional circumstances:*
  - If there are no reports in the system, the dashboard shows zero counts and the message "No reports have been submitted yet."
  - If there are many reports, the table is paginated (for example, 25 per page) so the page stays fast.
  - If the data cannot be loaded, an error banner explains the problem and offers a **Retry** button.

- [ ] 10. **Administrator filters and searches reports.**
  Above the reports table on the administrator dashboard, the administrator has
  a toolbar with a **Category** drop-down, a **Status** drop-down, an
  **Assigned To** drop-down (including an "Unassigned" option), and a keyword
  **Search** box that matches text in the title, description, and location. For
  example, the administrator can select *Category: Plumbing* and
  *Status: Reported* to see every new plumbing problem, or type "Building B" to
  see all problems reported in that building. Filters can be combined, the table
  updates as soon as a filter changes, and a label such as "Showing 4 of 57
  reports" confirms how many results matched. A **Clear Filters** button returns
  to the full list.
  *Exceptional circumstances:*
  - If no reports match the chosen filters, the table shows "No reports match your filters," along with a **Clear Filters** button.
  - Search text is treated strictly as text: special characters are safely handled and cannot be used to alter database queries.

- [ ] 11. **Administrator assigns a report to a responsible person.**
  From a report's details page, the administrator sees everything the resident
  submitted (description, category, location, photo, and submitter's name) plus
  an **Assignment** panel. The administrator selects the person responsible from
  an **Assign To** drop-down list of staff and maintenance contacts, such as
  "J. Martinez – Maintenance," optionally adds a short note like "Please check
  the breaker first," and clicks **Assign**. The system saves the assignment, and
  if the report was in the **Reported** status, automatically changes it to
  **Assigned**. The change is recorded in the report history (use case 14), the
  assigned person's name appears on the report in the dashboard table, and the
  resident sees the updated status and assignment the next time they view their
  report. The administrator can later reassign the report to a different person
  in the same way.
  *Exceptional circumstances:*
  - If the administrator clicks **Assign** without choosing a person, the system shows "Please select a person to assign this report to."
  - If two administrators update the same report at nearly the same time, the system saves the latest change, records both in the history, and shows the second administrator a notice that the report was just updated so they can review it.
  - Reports with the status **Resolved** cannot be reassigned unless they are first reopened (see use case 12).

- [ ] 12. **Administrator updates the status of a report.**
  On the report details page, the administrator uses the **Status** control to
  move the report through its lifecycle: **Reported → Assigned → In Progress →
  Resolved**. For example, when maintenance begins work on the broken light, the
  administrator changes the status to **In Progress**; when the light is fixed,
  they change it to **Resolved** and add a resolution note such as "Bulb and
  fixture replaced on Oct 4." The system saves the new status, timestamps it,
  records who made the change, and adds an entry to the report history. The
  updated colored badge appears immediately on the administrator dashboard and
  on the resident's **My Reports** page and report timeline. If a problem
  returns, the administrator can reopen a resolved report by setting it back to
  **In Progress**, and the reopening is recorded in the history as well.
  *Exceptional circumstances:*
  - A report cannot be marked **Assigned** or **In Progress** unless someone is assigned to it; if the administrator tries, the system shows "Assign this report to someone before changing its status."
  - Marking a report **Resolved** requires a short resolution note so the resident understands what was done; the system will not save the change without it.
  - Choosing the same status the report already has does nothing and creates no history entry.
  - If saving fails because of a server error, the status shown on the page reverts to the last saved value and the administrator sees "The status could not be updated. Please try again."

- [ ] 13. **System protects user credentials and personal information.**
  FixIt protects every account without the user needing to do anything. When a
  user creates an account, the system never stores the password itself; instead
  it stores a salted hash created with a strong one-way hashing algorithm
  (scrypt, using Werkzeug), so even someone who viewed the database could not read users'
  passwords. During login, the system uses the password verification helper to check
  it against the stored hash. After a successful login, the system issues a session
  token that is stored in a secure, HTTP-only cookie (so browser scripts cannot
  read it) and that expires after a period of inactivity. All traffic between
  the browser and server is sent over HTTPS so passwords, locations, and photos
  cannot be intercepted. Passwords and password hashes are never returned by the
  API or shown on any page, and database credentials and other secrets are kept
  in server environment variables, not in the source code. The system collects
  only the information needed to report and track problems—name, email, and
  report details.
  *Exceptional circumstances:*
  - Repeated failed logins trigger a temporary lockout (see use case 2) to slow down password-guessing attacks.
  - Error messages never reveal whether an email address is registered or expose internal system details such as database errors; detailed errors are written only to server logs.

- [ ] 14. **System enforces role-based access to features and data.**
  Every request that reaches the FixIt server is checked for two things: who the
  user is (authentication) and what their role allows (authorization). Residents
  may create reports and view only the reports they submitted. Administrators may
  view all reports, filter them, assign them, and change their status. These rules
  are enforced on the server for every API request, not just by hiding buttons in
  the interface, so a resident who tries to call an administrator function
  directly is still blocked. Likewise, when a resident requests a report, the
  server confirms that the report belongs to that resident before returning it.
  *Exceptional circumstances:*
  - A request without a valid session is rejected and the user is redirected to the login page.
  - A resident who attempts to reach an administrator page or action (for example, by typing the dashboard URL) sees "You do not have permission to access this page" and is returned to **My Reports**; the attempt is logged on the server.

- [ ] 15. **System validates and sanitizes all submitted information.**
  Whenever a user submits a form—signing up, logging in, reporting a problem,
  uploading a photo, assigning a report, or changing a status—the system checks
  the data twice: first in the browser, so the user gets immediate, friendly
  feedback, and again on the server, because browser checks can be bypassed. The
  server confirms that required fields are present, text is within length limits,
  categories and statuses are one of the allowed values, emails are well formed,
  and uploaded files really are images within the size limit. All database
  queries use parameterized statements to prevent SQL injection, and any text
  that users entered is escaped before being displayed so that it cannot run as
  code in another user's browser (preventing cross-site scripting). Uploaded
  photos are given new, system-generated file names so a user cannot overwrite
  other files.
  *Exceptional circumstances:*
  - If invalid data reaches the server (for example, a category value that doesn't exist), the server rejects the request with a clear error message, saves nothing, and the interface displays the message next to the relevant field.
  - If a file claims to be an image but its contents are not a valid image, the upload is rejected.

- [ ] 16. **System records the history of every report.**
  Each time something important happens to a report, the system automatically
  adds a permanent entry to that report's history: when it was created, every
  status change, every assignment or reassignment, and any notes added by an
  administrator. Each entry stores the date and time, the action taken, the old
  and new values (for example, "Status changed from Assigned to In Progress"),
  and which user made the change. History entries cannot be edited or deleted
  through the application, which makes the record trustworthy. Residents see this
  history as the **Progress Timeline** on their report (use case 8), and
  administrators see the full history, including who made each change, on the
  administrator report details page, helping them understand how long problems
  take to resolve and spot reports that have stalled.
  *Exceptional circumstances:*
  - The status change and its history entry are saved together in a single database transaction; if one cannot be saved, neither is, so the history and current status always agree.

- [ ] 17. **User accesses FixIt from a phone, tablet, or computer.**
  Because people often notice problems while they are out walking around,
  FixIt is a responsive web application that works in any modern browser without
  installing an app. On a phone, the navigation collapses into a menu button,
  the report form becomes a single column with large, easy-to-tap fields and
  buttons, and the photo button opens the phone's camera. On a tablet or desktop,
  residents and administrators see wider layouts, and the administrator's report
  list appears as a sortable table. Status colors are always paired with text
  labels so the information is understandable for users with color-vision
  differences, and form fields have labels that work with screen readers.
  *Exceptional circumstances:*
  - If the user's connection drops while using the site, the page shows a message that the connection was lost instead of failing silently, and any form in progress remains on screen so the user can resubmit when the connection returns.
  - If a user opens FixIt in an unsupported, very old browser, they see a message recommending an up-to-date browser.
