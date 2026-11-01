// Private, independently selectable task-ordering prototype; not full Yarn enforcement.
package io.github.apdelrahman1911.nativecmpkit.buildlogic

import org.gradle.api.Action
import org.gradle.api.DefaultTask
import org.gradle.api.GradleException
import org.gradle.api.Project
import org.gradle.api.tasks.TaskAction
import org.gradle.work.DisableCachingByDefault
import org.jetbrains.kotlin.gradle.targets.js.yarn.YarnLockUpgradeTask

/** No success outputs/stamp, filesystem reads, Project capture or graph query in the task action. */
@DisableCachingByDefault(because = "The ordinary-mode denial must execute fresh and never succeeds")
abstract class RefuseOrdinaryYarnUpgradeTask : DefaultTask() {
    @TaskAction
    fun refuseUpgrade() {
        throw GradleException("NCYUG-actual-upgrade-forbidden-before-root-task-actions")
    }
}

/**
 * Small independent negative prototype, NOT a reader/closure/tooling/argv/security implementation.
 * The gate is only selected through an actual YarnLockUpgradeTask dependency. mustRunAfter does
 * not select it in ordinary non-upgrade graphs. All root-build task actions are ordered after it
 * when present, including the shared primary install that KGP can force through graph membership.
 * Exclusions and configuration cache are explicitly unsupported for this ENTIRE opted-in run.
 * Real KGP schedule/negative tests remain pending. Included-build/configuration actions are outside
 * this root-build action-order claim. Bootstrap is held, not a property-level bypass.
 */
object OrdinaryYarnUpgradeTaskGate {
    private fun <T : Any> action(block: (T) -> Unit): Action<T> = object : Action<T> {
        override fun execute(target: T) = block(target)
    }

    fun install(root: Project) {
        require(root === root.rootProject) { "NCYUG-root-only" }
        val start = root.gradle.startParameter
        if (start.isConfigurationCacheRequested) refuse("configuration-cache-prototype-unsupported")
        if (start.excludedTaskNames.isNotEmpty()) refuse("exclusions-prototype-unsupported")
        if (start.isConfigureOnDemand) refuse("configure-on-demand-prototype-unsupported")
        if (root.providers.gradleProperty("nativecmpkit.yarnMode").orElse("ordinary").get() != "ordinary") {
            refuse("bootstrap-and-unknown-modes-held")
        }
        val gate = root.tasks.register("nativeCmpkitRefuseOrdinaryYarnUpgrade", RefuseOrdinaryYarnUpgradeTask::class.java,
            action { task ->
                task.group = "verification"
                task.description = "Refuse actual ordinary Yarn upgrade graphs before root-build task actions"
            })
        // Registration observers precede the child targets that late-apply KGP's root plugins.
        root.allprojects(action { project ->
            project.tasks.configureEach(action { task ->
                // Do not give the dependency-free gate a self-ordering edge.
                if (task !is RefuseOrdinaryYarnUpgradeTask) task.mustRunAfter(gate)
            })
            project.tasks.withType(YarnLockUpgradeTask::class.java).configureEach(action { upgrade ->
                upgrade.dependsOn(gate)
            })
        })
    }

    private fun refuse(code: String): Nothing = throw GradleException("NCYUG-$code")
}
