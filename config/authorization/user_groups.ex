alias Acl.Accessibility.Always, as: AlwaysAccessible
alias Acl.GraphSpec.Constraint.ResourceFormat, as: ResourceFormatConstraint
alias Acl.GraphSpec.Constraint.Resource, as: ResourceConstraint
alias Acl.GraphSpec, as: GraphSpec
alias Acl.GroupSpec, as: GroupSpec
alias Acl.GroupSpec.GraphCleanup, as: GraphCleanup

defmodule Acl.UserGroups.Config do
  def user_groups do
    [
      # // PUBLIC
      %GroupSpec{
        name: "public",
        useage: [:read,:write,:read_for_write],
        access: %AlwaysAccessible{},
        graphs: [ %GraphSpec{
                    graph: "http://mu.semte.ch/graphs/docker",
                    constraint: %ResourceConstraint{
                      resource_types: [
                        "https://w3.org/ns/bde/docker#Container",
                        "https://w3.org/ns/bde/docker#ContainerLabel",
                        "https://w3.org/ns/bde/docker#State",
                        "http://mu.semte.ch/vocabularies/ext/docker-logger/NetworkMonitor"
                      ]
                    } }
                ] },

      %GraphCleanup{
        originating_graph: "http://mu.semte.ch/application",
        useage: [:write],
        name: "clean"
      }
    ]
  end
end
