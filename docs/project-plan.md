# Project Plan

## 1. Title and Tagline - What is the project called, and what's it about?

The title of this project is *FixIt - Report It. Track It. Get It
Fixed.*

FixIt is a web-based community problem reporting and tracking system
that allows users to report issues and follow their progress from
initial submission through resolution.

## 2. Problem - What problem are we solving?

Problems in ablems, or broken equipment may remain unresolved
for days or weeks.partment communities, college campuses, and local
neighborhoods often go unreported or unresolved because people may not
know who to contact or because the reporting process is inconvenient.
Issues such as broken lights, damaged sidewalks, overflowing trash cans,
potholes, plumbing pro

Reports may also be scattered across phone calls, emails, text messages,
or informal conversations, making them difficult for administrators to
organize and track.

FixIt will provide one centralized system where users can report
problems and monitor their status. Administrators will be able to review
reported problems, assign them, update their status, and keep track of
unresolved issues. This will make communication between community
members and administrators more organized and transparent.

## 3. Users - Who is this for?

FixIt is intended for people who need a simple way to report problems
within a community or organization.

Potential users include residents of apartment communities, college
students and staff, neighborhood residents, and members of other small
communities.

The application will have two primary types of users:

-   **Regular Users** - Can create an account, report an issue, provide
    information about the problem, upload a photo, specify its location,
    and track the status of their submitted reports.
-   **Administrators** - Can view reported issues, filter and manage
    reports, assign issues, and update their status as work progresses.

The MVP will focus on these two user roles rather than creating multiple
specialized administrative or maintenance roles.

## 4. Team members - Who is working on this and how are they qualified?

The following person is working on this project:

-   **Anjaliben Valand:** Anjaliben will develop FixIt as an individual
    capstone project. She has experience with software development
    technologies including front-end development, back-end development,
    databases, and web application development. She will be responsible
    for planning the application, developing the user interface and
    backend, designing the database, integrating the different parts of
    the system, testing the application, and deploying the completed
    project.

Because this is an individual project, the MVP will focus on the most
important reporting and tracking functionality while keeping the scope
manageable within the semester.

## 5. Features - What does the MVP need?

-   **User Accounts and Login** - Users will be able to create an
    account and log in so that submitted reports can be associated with
    them.
-   **Issue Reporting** - Users will be able to submit a problem with a
    title or short description, category, location, and additional
    details.
-   **Photo Uploads** - Users will be able to attach a photo to a report
    to help administrators understand the reported problem.
-   **Issue Categories** - Reports can be organized into categories such
    as lighting, roads and sidewalks, trash, plumbing, equipment, and
    other common community problems.
-   **Issue Status Tracking** - Each report will have a status such as
    "Reported," "Assigned," "In Progress," or "Resolved."
-   **User Dashboard** - Users will be able to view the issues they have
    submitted and see the current status of each report.
-   **Report Details** - Users will be able to open a report and review
    its description, category, location, photo, and current status.
-   **Administrator Dashboard** - Administrators will be able to view
    and manage reports submitted through the system.
-   **Filtering and Searching** - Administrators will be able to filter
    issues based on information such as category or status, making it
    easier to find unresolved or related problems.
-   **Issue Assignment** - Administrators will be able to assign
    reported problems to a person responsible for handling them.
-   **Status Updates** - Administrators will be able to update an issue
    as it moves from reported to assigned, in progress, and resolved.
-   **Report History** - Important changes to an issue, particularly
    status updates, will be stored so progress can be tracked.

Explicitly excluded from the MVP:

-   Interactive maps showing all reported problems
-   Email, text message, or push notifications
-   Advanced analytics and reporting
-   Automatic issue categorization
-   Automatic detection of duplicate reports
-   User voting or upvoting of community problems
-   Native Android or iOS applications

These features may be considered after the initial version is completed.

## 6. Data - What are we storing?

FixIt will store information needed to manage users and community
problem reports.

The main data will include:

-   User information such as name, email address, password information,
    and role
-   Issue title and description
-   Issue category
-   Issue location
-   Uploaded photo information
-   Current issue status
-   Person assigned to an issue
-   Date and time the report was submitted
-   Status and update history

The application will use a database to connect reports with the users
who submitted them and maintain their status over time. Uploaded images
may be stored separately from the database, with the database
maintaining a reference to each image.

There are privacy concerns because reports may contain account
information, photographs, and location information. FixIt will use
authentication and role-based authorization to restrict access to
appropriate functionality. Passwords will not be stored as plain text,
and user input will be validated before being processed or stored. The
application will collect only the information needed to provide its
reporting and tracking functionality.

## 7. Tech - What stack are we using?

The planned technology stack for FixIt includes:

-   **React** for building the web-based user interface
-   **HTML5 and CSS3** for page structure and responsive styling
-   **JavaScript** for client-side application functionality, with Vite and npm for frontend development
-   **Python and Flask** for the backend server and application APIs
-   **PostgreSQL** for storing users, reports, categories, statuses,
    assignments, and report history
-   **Flask-SQLAlchemy and psycopg** for database access, with Flask-Migrate for schema changes
-   **pytest and the Flask test client** for backend testing
-   **Database-backed authentication sessions with Flask-signed cookies** for login, and **Werkzeug** for password hashing
-   **Pillow** for checking uploaded images
-   **REST APIs** for communication between the React frontend and
    backend
-   **Authentication and role-based authorization** for controlling
    access for regular users and administrators
-   **Image upload/storage functionality** for photographs attached to
    reports
-   **Git and GitHub** for source control and project management

The application will use a web-based architecture so users can access
FixIt through a modern browser on a computer, tablet, or smartphone.

## 8. Related work - Who has done similar work before?

Several existing applications provide ways for residents to report
problems to local governments and organizations.

-   **SeeClickFix** - SeeClickFix is a community issue-reporting
    platform that allows residents to report non-emergency problems and
    communicate with local organizations. It demonstrates how reports
    can be organized by location and status and how users can receive
    visibility into the progress of community issues.
-   **311 Systems** - Many cities provide 311 services that allow
    residents to report non-emergency problems such as potholes,
    graffiti, damaged public property, and trash-related issues. These
    systems demonstrate the usefulness of having a centralized location
    for submitting and managing service requests.
-   **Campus and Maintenance Request Systems** - Colleges, apartment
    complexes, and other organizations commonly provide maintenance
    request systems where users submit problems and staff members manage
    the requests. These systems demonstrate how reporting and work
    tracking can be useful even within smaller communities.

FixIt will use ideas from these existing systems, particularly
centralized reporting, issue categorization, status tracking, and
administrative management. However, the project will focus on creating a
simpler system appropriate for smaller communities such as apartment
complexes, college campuses, and neighborhoods.

## 9. Monetize - How will this make money?

Monetization will not be included in the MVP because the main goal of
the project is to develop and demonstrate a functional community
issue-reporting system.

If FixIt were developed into a commercial product, it could use a
subscription-based model. Apartment complexes, colleges, homeowners
associations, property management companies, or other organizations
could pay a monthly or yearly fee to use the platform. Different
subscription levels could eventually be offered based on the number of
users, administrators, properties, or advanced features required.

## 10. UI/UX - How should this look and feel?

FixIt will have a clean, simple, and modern web interface designed to
make reporting a problem quick and easy. The interface will be
responsive so it can be used comfortably on both desktop computers and
mobile devices.

The overall design will use a simple color scheme with clear visual
indicators for issue status. For example, different status labels can
make it easy for users to recognize whether an issue is reported,
assigned, in progress, or resolved.

Users will see a straightforward form when reporting an issue and a
dashboard showing their previously submitted reports. Reports will be
displayed in an organized format that makes the category, status, and
other important information easy to understand.

Administrators will have a dashboard focused on managing reports. The
interface will emphasize readability and simple navigation so
administrators can quickly identify unresolved issues, filter reports,
assign work, and update progress.

The overall goal of the UI/UX is to minimize the number of steps
required to report a problem while making issue progress easy to
understand.

## 11. Deployment - Where and how will this ship?

FixIt will be deployed as a web application, so users will not need to
install special software on their computers or phones. They will access
the application through a web browser using a URL.

The React frontend and Python/Flask backend will be hosted using a
cloud-based platform that supports Python, using a production WSGI server such as Gunicorn. The React build and API will be served under the same site origin. The PostgreSQL database will also be
hosted online so application data can be accessed securely by the
backend.

Uploaded images will be stored using an appropriate server or cloud
storage solution. Configuration information and sensitive credentials
will be managed through environment variables rather than being included
directly in the source code.

Once deployed, users will be able to access FixIt from desktop and
mobile web browsers, create an account, submit reports, and track their
issues, while administrators will be able to manage those reports
through the administrative interface.
