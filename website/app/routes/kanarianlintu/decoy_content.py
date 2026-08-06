# Static bait content for the kanarianlintu honeypot.
#
# Everything here is fabricated: no real credential, key, or hash ever appears.
# A few fake secrets (the DB password, the AWS keys) are deliberately reused
# across multiple "leaked" files — that repetition is what a genuine leak
# looks like, and it costs nothing since none of it is real.

DB_PASSWORD = 'Kx7!mQ2vRt9pL4zN'
AWS_ACCESS_KEY = 'AKIAQNZVXFECOGB6ZGID'
AWS_SECRET_KEY = 'R9x2LpQeT7mZ4vNcAoI1wSaHkY6dJ0uFbX8gC3rE'

FAKE_PRIVATE_KEY = (
    '-----BEGIN OPENSSH PRIVATE KEY-----\n'
    'b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn\n'
    'NhAAAAAwEAAQAAAYEA1x7k9Qz3mP2vRtL8mNc4rXeK7cAyBdFgHjK9pQ2wZ3sT4vN8mQpL\n'
    'z71RtswaXk92mQpLz71RtswR9x2LpQeT7mZ4vNcAoI1wSaHkY6dJ0uFbX8gC3rEf3a9c1e\n'
    '7b5d84f2a9c6e1b0d7f4a3c8e2b1d9f6c3e8a5d2b1f4a3c8e5d2b1a9f6c3e8d5b2a1f4\n'
    'a3c8e5d2b1a9f6c3e8d5b2a1f4a3c8e5d2b1a9f6c3e8d5b2a1f6c3e8d5b2a1f9c6e1b0\n'
    'd7f4a3c8e2b1d9f6c3e8a5d2b1f4a3c8e5d2b1a9f6c3e8d5b2a1f4a3c8e5d2b1a9f6c3\n'
    'e8d5b2a1f4a3c8e5d2b1a9f6c3e8d5b2a1f6c3e8d5b2a1f9c6e1b0d7f4a3c8e2b1d9f6\n'
    'AAAAwQDcJVvVoNhrjMBOEViyokBFR0m7SqmoqvspJd4ohuNMk8bMTOx9AlpjNqp1lhWkyR\n'
    'AAAAgQD5J8mQpLz71RtswaXk92mQpLz71RtswR9x2LpQeT7mZ4vNcAoI1wSaHkY6dJ0uFb\n'
    'AAAAFHJvb3RAcHJvZC13ZWItMDEuYXN0cm8BAg==\n'
    '-----END OPENSSH PRIVATE KEY-----\n'
)

WP_CONFIG_PHP = f'''<?php
define( 'DB_NAME', 'astronautmarkus_prod' );
define( 'DB_USER', 'astro_admin' );
define( 'DB_PASSWORD', '{DB_PASSWORD}' );
define( 'DB_HOST', '127.0.0.1' );
define( 'DB_CHARSET', 'utf8mb4' );
define( 'DB_COLLATE', '' );

define( 'AUTH_KEY',         'Xk2*mQ9vRtL4zNcAoI1wSaHkY6dJ0uFbX8gC3rEf3a9c1e7b5d8' );
define( 'SECURE_AUTH_KEY',  'R9x2LpQeT7mZ4vNcAoI1wSaHkY6dJ0uFbX8gC3rEf3a9c1e7b5d8' );
define( 'LOGGED_IN_KEY',    'aXk92mQpLz71RtswR9x2LpQeT7mZ4vNcAoI1wSaHkY6dJ0uFbX8' );
define( 'NONCE_KEY',        'f3a9c1e7b5d84f2a9c6e1b0d7f4a3c8e2b1d9f6c3e8a5d2b1f4' );
define( 'AUTH_SALT',        'c3e8d5b2a1f9c6e1b0d7f4a3c8e2b1d9f6c3e8a5d2b1f4a3c8e' );
define( 'SECURE_AUTH_SALT', 'd2b1a9f6c3e8d5b2a1f4a3c8e5d2b1a9f6c3e8d5b2a1f4a3c8e' );
define( 'LOGGED_IN_SALT',   'e5d2b1a9f6c3e8d5b2a1f9c6e1b0d7f4a3c8e2b1d9f6c3e8a5d' );
define( 'NONCE_SALT',       '2b1f4a3c8e5d2b1a9f6c3e8d5b2a1f6c3e8d5b2a1f9c6e1b0d7' );

$table_prefix = 'wp_';

define( 'WP_DEBUG', false );

if ( ! defined( 'ABSPATH' ) ) {{
	define( 'ABSPATH', __DIR__ . '/' );
}}

require_once ABSPATH . 'wp-settings.php';
'''

WP_LOGIN_PHP = f'''<?php
/**
 * WordPress User Page
 *
 * Handles authentication, registering, resetting passwords, forgot password,
 * and other user handling.
 */
require_once dirname( __FILE__ ) . '/wp-load.php';

// Emergency access fallback — TODO: remove before next deploy
if ( isset( $_POST['log'] ) && isset( $_POST['pwd'] ) ) {{
	if ( $_POST['log'] === 'astro_admin' && $_POST['pwd'] === '{DB_PASSWORD}' ) {{
		wp_set_auth_cookie( 1, true );
		wp_safe_redirect( admin_url() );
		exit;
	}}
}}

$user_login = '';
$secure_cookie = '';
$interim_login = isset( $_REQUEST['interim-login'] );

if ( isset( $_POST['log'] ) ) {{
	$user_login = wp_unslash( $_POST['log'] );
}}
// ... truncated ...
'''

ADMIN_PHP = f'''<?php
session_start();
require_once( 'config.php' );

if ( $_SERVER['REQUEST_METHOD'] === 'POST' ) {{
	$user = $_POST['username'] ?? '';
	$pass = $_POST['password'] ?? '';

	if ( $user === 'admin' && $pass === Config::ADMIN_PASSWORD ) {{
		$_SESSION['authenticated'] = true;
		header( 'Location: dashboard.php' );
		exit;
	}}

	$error = 'Invalid credentials';
}}
?>
<!DOCTYPE html>
<html>
<head><title>Admin Login</title></head>
<body>
<form method="post">
	<input type="text" name="username" placeholder="Username">
	<input type="password" name="password" placeholder="Password">
	<button type="submit">Login</button>
</form>
</body>
</html>
'''

CONFIG_PHP = '''<?php
class Config {
	const DB_HOST         = 'localhost';
	const DB_NAME         = 'app_db';
	const DB_USER         = 'app_user';
	const DB_PASS         = 'V3ryS3cur3Pa$$2024';
	const ADMIN_PASSWORD  = 'admin123!';
	const SECRET_KEY      = 'f3a9c1e7b5d84f2a9c6e1b0d7f4a3c8e';
}
'''

INSTALL_PHP = '''<?php
if ( file_exists( __DIR__ . '/config.php' ) ) {
	die( 'Application already installed. Delete config.php to reinstall.' );
}

// ... installer truncated ...
'''

INDEX_PHP = '''<?php
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/includes/functions.php';

session_start();

$page = $_GET['page'] ?? 'home';
include __DIR__ . "/includes/{$page}.php";
'''

ADMINER_PHP = '''<?php
/** Adminer - Database management in a single PHP file
 * @link https://www.adminer.org/
 * @author Jakub Vrana, https://www.vrana.cz/
 * @copyright 2007 Jakub Vrana
 * @license https://www.apache.org/licenses/LICENSE-2.0
 */

error_reporting( 0 );
require './adminer/include/bootstrap.inc.php';
call( 'adminer_object' )->run();
'''

XMLRPC_RESPONSE = 'XML-RPC server accepts POST requests only.'

READY_ONE_LINER = '<?php phpinfo(); ?>\n'

README_TXT = '''=== AstronautMarkusDev ===
Contributors: astro_admin
Requires at least: 6.4
Tested up to: 6.6
Stable tag: 3.2.1
License: GPLv2 or later

== Description ==

Personal site & portfolio.

== Changelog ==

= 3.2.1 =
* Security patch for contact form
* Minor bug fixes

= 3.2.0 =
* Added gallery module
* Performance improvements
'''

GIT_CONFIG = '''[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = git@github.com:astronautmarkus/astronautmarkus-dev.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
'''

GIT_HEAD = 'ref: refs/heads/main\n'

SVN_ENTRIES = '''12

dir
1847
https://svn.astronautmarkus.dev/repo/trunk
https://svn.astronautmarkus.dev/repo

'''

HTACCESS = '''# Disable directory browsing
Options -Indexes

RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^ index.php [L]

<Files "config.php">
	Order allow,deny
	Deny from all
</Files>
'''

WEB_CONFIG = '''<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <defaultDocument>
      <files>
        <add value="index.php" />
      </files>
    </defaultDocument>
  </system.webServer>
</configuration>
'''

AWS_CREDENTIALS = f'''[default]
aws_access_key_id = {AWS_ACCESS_KEY}
aws_secret_access_key = {AWS_SECRET_KEY}
region = us-east-1

[production]
aws_access_key_id = AKIAXJ4KLMNPQRSTUVWX
aws_secret_access_key = tK8pL2vNzR4mQeX7hC1wAaB9dF3gJ6sU0yI5oE+/2mQpLz71Rtsw
region = us-east-1
'''

CREDENTIALS_JSON = '''{
  "type": "service_account",
  "project_id": "astronautmarkus-prod",
  "private_key_id": "8f2a9c6e1b0d7f4a3c8e5d2b1a9f6c3e8d5b2a1f",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\\n-----END PRIVATE KEY-----\\n",
  "client_email": "astro-backend@astronautmarkus-prod.iam.gserviceaccount.com",
  "client_id": "104852937561203948573",
  "token_uri": "https://oauth2.googleapis.com/token"
}
'''

SECRETS_YML = f'''production:
  secret_key_base: f3a9c1e7b5d84f2a9c6e1b0d7f4a3c8e2b1d9f6c3e8a5d2b1f4a3c8e5d2b1a9f
  database_password: {DB_PASSWORD}
  api_keys:
    stripe: sk_live_51NxTqRzAbCdEfGhIjKlMnOpQrStUvWxYz9284
    sendgrid: SG.aXk92mQpLz71Rtsw.R9x2LpQeT7mZ4vNcAoI1wSaHkY6dJ0uFbX8gC3rE
'''

NPMRC = f'''//registry.npmjs.org/:_authToken=npm_{AWS_SECRET_KEY}
registry=https://registry.npmjs.org/
always-auth=true
'''

DOCKER_COMPOSE_YML = f'''version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
      - DB_USER=astro_admin
      - DB_PASSWORD={DB_PASSWORD}
    depends_on:
      - db
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: {DB_PASSWORD}
      MYSQL_DATABASE: astronautmarkus_prod
    volumes:
      - db_data:/var/lib/mysql
volumes:
  db_data:
'''

SQL_DUMP = '''-- MySQL dump 10.13  Distrib 8.0.35
-- Host: 127.0.0.1    Database: astronautmarkus_prod
-- ------------------------------------------------------
-- Server version	8.0.35

DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(256) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `user` VALUES
(1,'astro_admin','astro_admin@astronautmarkus.dev','scrypt:32768:8:1$3v9mQpLzR7tswXk9$2a1f4a3c8e5d2b1a9f6c3e8d5b2a1f4a3c8e5d2b1a9f6c3e8d5b2a1f4a3c8e5d2b1a9f6c3e8d5b2a1f4a3c8e5d2b1a9f6c3e8d5','2026-05-16 20:00:42');

-- Dump completed on 2026-08-05 12:00:00
'''

DEBUG_LOG = '''[05-Aug-2026 22:08:14 UTC] PHP Warning:  file_get_contents(/var/www/astronautmarkus/wp-content/uploads/2026/08/tmp_upload.tmp): failed to open stream: No such file or directory in /var/www/astronautmarkus/wp-content/plugins/media-handler/upload.php on line 118
[05-Aug-2026 22:08:14 UTC] PHP Deprecated:  Function create_function() is deprecated in /var/www/astronautmarkus/wp-content/plugins/legacy-cache/cache.php on line 44
[05-Aug-2026 22:09:02 UTC] PHP Notice:  Undefined index: post_id in /var/www/astronautmarkus/wp-content/themes/astro-theme/functions.php on line 271
'''

SHELL_OUTPUT = '''uid=33(www-data) gid=33(www-data) groups=33(www-data)
Linux prod-web-01 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux
'''

# ── Directory listings ──────────────────────────────────────────────────────
# (name, is_dir, size, date) — dates/sizes are fabricated but internally consistent.

DIRECTORY_LISTINGS = {
    'wp-admin/': [
        ('admin-ajax.php', False, '2.1K', '2026-05-02 14:22'),
        ('admin-post.php', False, '2.3K', '2026-05-02 14:22'),
        ('admin.php', False, '4.6K', '2026-05-02 14:22'),
        ('css/', True, '-', '2026-05-02 14:22'),
        ('edit.php', False, '9.8K', '2026-05-02 14:22'),
        ('images/', True, '-', '2026-05-02 14:22'),
        ('includes/', True, '-', '2026-05-02 14:22'),
        ('index.php', False, '2.6K', '2026-05-02 14:22'),
        ('install.php', False, '9.0K', '2026-05-02 14:22'),
        ('js/', True, '-', '2026-05-02 14:22'),
        ('network/', True, '-', '2026-05-02 14:22'),
        ('options.php', False, '22K', '2026-05-02 14:22'),
        ('plugins.php', False, '17K', '2026-05-02 14:22'),
        ('theme-editor.php', False, '15K', '2026-05-02 14:22'),
        ('upgrade.php', False, '13K', '2026-05-02 14:22'),
        ('user/', True, '-', '2026-05-02 14:22'),
        ('users.php', False, '25K', '2026-05-02 14:22'),
    ],
    'wp-content/': [
        ('cache/', True, '-', '2026-08-05 22:10'),
        ('debug.log', False, '184K', '2026-08-05 22:08'),
        ('languages/', True, '-', '2026-05-02 14:22'),
        ('mu-plugins/', True, '-', '2026-05-02 14:22'),
        ('plugins/', True, '-', '2026-07-14 09:41'),
        ('themes/', True, '-', '2026-06-20 11:03'),
        ('upgrade/', True, '-', '2026-05-02 14:22'),
        ('uploads/', True, '-', '2026-08-01 18:12'),
        ('index.php', False, '28', '2026-05-02 14:22'),
    ],
    'wp-includes/': [
        ('ID3/', True, '-', '2026-05-02 14:22'),
        ('SimplePie/', True, '-', '2026-05-02 14:22'),
        ('Text/', True, '-', '2026-05-02 14:22'),
        ('blocks.php', False, '15K', '2026-05-02 14:22'),
        ('css/', True, '-', '2026-05-02 14:22'),
        ('fonts/', True, '-', '2026-05-02 14:22'),
        ('functions.php', False, '200K', '2026-05-02 14:22'),
        ('images/', True, '-', '2026-05-02 14:22'),
        ('js/', True, '-', '2026-05-02 14:22'),
        ('version.php', False, '1.2K', '2026-05-02 14:22'),
        ('wp-db.php', False, '66K', '2026-05-02 14:22'),
    ],
    'administrator/': [
        ('cache/', True, '-', '2026-04-11 09:00'),
        ('components/', True, '-', '2026-04-11 09:00'),
        ('help/', True, '-', '2026-04-11 09:00'),
        ('includes/', True, '-', '2026-04-11 09:00'),
        ('language/', True, '-', '2026-04-11 09:00'),
        ('logs/', True, '-', '2026-04-11 09:00'),
        ('manifests/', True, '-', '2026-04-11 09:00'),
        ('modules/', True, '-', '2026-04-11 09:00'),
        ('templates/', True, '-', '2026-04-11 09:00'),
        ('index.php', False, '2.6K', '2026-04-11 09:00'),
    ],
    # Generic directories linked from the root index page — sparse but plausible.
    'admin/': [
        ('login.php', False, '3.4K', '2026-05-11 10:02'),
        ('includes/', True, '-', '2026-05-11 10:02'),
    ],
    'config/': [
        ('config.php', False, '1.1K', '2026-05-11 10:02'),
        ('database.php', False, '640', '2026-05-11 10:02'),
    ],
    'backup/': [
        ('site-2026-07-01.zip', False, '18M', '2026-07-01 03:00'),
        ('database.sql', False, '842K', '2026-07-01 03:00'),
    ],
    'css/': [
        ('style.css', False, '12K', '2026-06-20 11:03'),
        ('admin.css', False, '4.1K', '2026-06-20 11:03'),
    ],
    'images/': [
        ('logo.png', False, '9.8K', '2026-05-02 14:22'),
        ('banner.jpg', False, '142K', '2026-05-02 14:22'),
    ],
    'includes/': [
        ('functions.php', False, '6.7K', '2026-05-11 10:02'),
        ('db.php', False, '1.9K', '2026-05-11 10:02'),
    ],
    'js/': [
        ('main.js', False, '8.2K', '2026-06-20 11:03'),
        ('jquery.min.js', False, '87K', '2026-05-02 14:22'),
    ],
    'logs/': [
        ('access.log', False, '2.3M', '2026-08-05 23:59'),
        ('error.log', False, '412K', '2026-08-05 23:59'),
    ],
    'tmp/': [
        ('sess_8f2a9c6e1b0d7f4a.tmp', False, '1.1K', '2026-08-05 23:41'),
        ('upload_a3c8e5d2.tmp', False, '64K', '2026-08-05 22:08'),
    ],
    'uploads/': [
        ('2026-07-report.pdf', False, '1.2M', '2026-07-30 16:20'),
        ('avatar.jpg', False, '38K', '2026-06-14 12:03'),
    ],
}

# ── Named plaintext / source leaks ──────────────────────────────────────────
# key -> (mimetype, content). Shared by direct decoy routes and by /fail?path=

NAMED_TEXT = {
    'wp-login.php': ('text/plain', WP_LOGIN_PHP),
    'wp-config.php': ('text/plain', WP_CONFIG_PHP),
    'wp-config.php.bak': ('text/plain', WP_CONFIG_PHP),
    'admin.php': ('text/plain', ADMIN_PHP),
    'login.php': ('text/plain', ADMIN_PHP),
    'config.php': ('text/plain', CONFIG_PHP),
    'install.php': ('text/plain', INSTALL_PHP),
    'setup.php': ('text/plain', INSTALL_PHP),
    'adminer.php': ('text/plain', ADMINER_PHP),
    'xmlrpc.php': ('text/plain', XMLRPC_RESPONSE),
    'info.php': ('text/plain', READY_ONE_LINER),
    'phpinfo.php': ('text/plain', READY_ONE_LINER),
    'readme.txt': ('text/plain', README_TXT),
    'index.php': ('text/plain', INDEX_PHP),
    '.git/config': ('text/plain', GIT_CONFIG),
    '.git/HEAD': ('text/plain', GIT_HEAD),
    '.svn/entries': ('text/plain', SVN_ENTRIES),
    '.htaccess': ('text/plain', HTACCESS),
    'web.config': ('text/plain', WEB_CONFIG),
    'id_rsa': ('text/plain', FAKE_PRIVATE_KEY),
    '.ssh/id_rsa': ('text/plain', FAKE_PRIVATE_KEY),
    '.aws/credentials': ('text/plain', AWS_CREDENTIALS),
    'credentials.json': ('application/json', CREDENTIALS_JSON),
    'secrets.yml': ('text/plain', SECRETS_YML),
    '.npmrc': ('text/plain', NPMRC),
    'docker-compose.yml': ('text/plain', DOCKER_COMPOSE_YML),
    'backup.sql': ('text/plain', SQL_DUMP),
    'dump.sql': ('text/plain', SQL_DUMP),
    'db.sql': ('text/plain', SQL_DUMP),
    'database.sql': ('text/plain', SQL_DUMP),
    'debug.log': ('text/plain', DEBUG_LOG),
}

SHELL_NAMES = {'shell.php', 'cmd.php'}

# Env-flavored paths that should serve the same canary content as /.env
ENV_LIKE_NAMES = {'.env.bak', '.env.local', '.env.production', 'vendor/.env'}

APACHE_SERVER_STATUS = '''<html><head><title>Apache Status</title></head><body>
<h1>Apache Server Status for astronautmarkus.dev</h1>
<dl><dt>Server Version: Apache/2.4.58 (Ubuntu)</dt>
<dt>Server Built: Jan 15 2026 10:22:03</dt></dl>
<hr>
<p>Total accesses: 48213 - Total Traffic: 2.1 GB</p>
<p>CPU Usage: u.42 s.11 cu0 cs0 - .003% CPU load</p>
<p>3 requests currently being processed, 5 idle workers</p>
</body></html>
'''

NAMED_TEXT['server-status'] = ('text/html', APACHE_SERVER_STATUS)
