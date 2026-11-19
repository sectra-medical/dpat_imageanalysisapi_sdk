/** Information about a registered application. */
export interface Application {
    /**
     * Site unique ID of the application that will be used to reference the
     * application.
     */
    applicationId: string;

    /** Name to be displayed to end user. */
    displayName: string;

    /** Application manufacturer. */
    manufacturer: string;

    /**
     * Any context data that is needed by the called application. This data is
     * private to the app and included in all invocations (don't make it too
     * big). Needs to be a valid JSON object.
     */
    context?: string;
}

