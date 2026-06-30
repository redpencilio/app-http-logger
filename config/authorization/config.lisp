;;;;;;;;;;;;;;;;;;;
;;; delta messenger
(in-package :delta-messenger)

;; (push (make-instance 'delta-logging-handler) *delta-handlers*)
(add-delta-messenger "http://delta/")

;;;;;;;;;;;;;;;;;
;;; configuration
(in-package :client)
(setf *log-sparql-query-roundtrip* nil)
(setf *backend* "http://triplestore:8890/sparql")

(in-package :server)
(setf *log-incoming-requests-p* nil)

;;;;;;;;;;;;;;;;;
;;; access rights

(in-package :acl)

(defparameter *access-specifications* nil
  "All known ACCESS specifications.")

(defparameter *graphs* nil
  "All known GRAPH-SPECIFICATION instances.")

(defparameter *rights* nil
  "All known GRANT instances connecting ACCESS-SPECIFICATION to GRAPH.")

(define-prefixes
  :ext "http://mu.semte.ch/vocabularies/ext/"
  :docker "https://w3.org/ns/bde/docker#")

(define-graph public ("http://mu.semte.ch/graphs/docker")
  ("docker:Container" -> _)
  ("docker:ContainerLabel" -> _)
  ("docker:State" -> _)
  ("ext:docker-logger/NetworkMonitor" -> _))

(supply-allowed-group "public")

(grant (read write) :to-graph public :for-allowed-group "public")

